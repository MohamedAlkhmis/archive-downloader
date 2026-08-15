import json
import os
import subprocess
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
import shutil
import zipfile


CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")


def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return None


def save_credentials(creds):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def clear_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        os.remove(CREDENTIALS_FILE)


def login(email, password):
    data = urllib.parse.urlencode({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        "https://archive.org/services/xauthn/?op=login",
        data=data,
        headers={
            "User-Agent": ArchiveAPI.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            result = json.loads(body)
        except json.JSONDecodeError:
            return {"success": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    if result.get("success"):
        values = result.get("values", {})
        cookies = values.get("cookies", {})
        creds = {
            "email": email,
            "logged_in_user": cookies.get("logged-in-user", ""),
            "logged_in_sig": cookies.get("logged-in-sig", ""),
            "s3_access": values.get("s3", {}).get("access", ""),
            "s3_secret": values.get("s3", {}).get("secret", ""),
        }
        save_credentials(creds)
        return {"success": True, "email": email}
    else:
        reason = result.get("values", {}).get("reason", "Login failed")
        friendly = {
            "account_bad_password": "Wrong password",
            "account_not_found": "Account not found",
        }
        return {"success": False, "error": friendly.get(reason, reason)}


def get_auth_cookies():
    creds = load_credentials()
    if creds and creds.get("logged_in_user") and creds.get("logged_in_sig"):
        return f"logged-in-user={creds['logged_in_user']}; logged-in-sig={creds['logged_in_sig']}"
    return None


class ArchiveAPI:
    USER_AGENT = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    TIMEOUT = 30
    MAX_RETRIES = 2

    def _request(self, url, timeout=None):
        if timeout is None:
            timeout = self.TIMEOUT
        last_err = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                headers = {"User-Agent": self.USER_AGENT}
                cookies = get_auth_cookies()
                if cookies:
                    headers["Cookie"] = cookies
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                last_err = e
                if attempt < self.MAX_RETRIES:
                    time.sleep(1)
        raise last_err

    def search(self, query, page=1, rows=50):
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "description", "item_count", "downloads"],
            "sort[]": "downloads desc",
            "rows": str(rows),
            "page": str(page),
            "output": "json",
        }
        url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params, doseq=True)
        try:
            data = self._request(url)
            docs = data.get("response", {}).get("docs", [])
            total = data.get("response", {}).get("numFound", 0)
            return {"items": docs, "total": total, "page": page, "error": None}
        except Exception as e:
            return {"items": [], "total": 0, "page": page, "error": str(e)}

    def get_metadata(self, identifier):
        url = f"https://archive.org/metadata/{urllib.parse.quote(identifier)}"
        try:
            return self._request(url, timeout=45)
        except Exception as e:
            return {"error": str(e)}

    def get_files(self, identifier, extensions=None):
        meta = self.get_metadata(identifier)
        if "error" in meta and meta.get("files") is None:
            return {"files": [], "error": meta.get("error"), "login_required": False}

        server = meta.get("d1") or meta.get("d2") or meta.get("server", "")
        dir_path = meta.get("dir", "")

        collections = meta.get("metadata", {}).get("collection", [])
        if isinstance(collections, str):
            collections = [collections]
        login_required = "loggedin" in collections

        files = []
        for f in meta.get("files", []):
            name = f.get("name", "")
            ext = os.path.splitext(name)[1].lower()
            if extensions and ext not in extensions:
                continue
            size = int(f.get("size", 0)) if f.get("size") else 0
            if server and dir_path:
                url = f"https://{server}{dir_path}/{urllib.parse.quote(name)}"
            else:
                url = f"https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(name)}"
            files.append({
                "name": name,
                "size": size,
                "format": f.get("format", ""),
                "url": url,
            })
        files.sort(key=lambda x: x["name"].lower())
        return {"files": files, "error": None, "login_required": login_required}


QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.json")
BG_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.pid")


class Download:
    def __init__(self, url, dest_path, filename):
        self.url = url
        self.dest_path = dest_path
        self.filename = filename
        self.progress = 0.0
        self.total_bytes = 0
        self.downloaded_bytes = 0
        self.speed = 0
        self.status = "pending"
        self.error = None
        self.start_time = 0

    def eta_seconds(self):
        if self.speed <= 0 or self.total_bytes <= 0:
            return -1
        remaining = self.total_bytes - self.downloaded_bytes
        if remaining <= 0:
            return 0
        return int(remaining / self.speed)

    def to_dict(self):
        return {
            "url": self.url,
            "dest_path": self.dest_path,
            "filename": self.filename,
            "status": self.status,
            "error": self.error,
            "total_bytes": self.total_bytes,
            "downloaded_bytes": self.downloaded_bytes,
        }

    @staticmethod
    def from_dict(d):
        dl = Download(d["url"], d["dest_path"], d["filename"])
        dl.status = d.get("status", "pending")
        dl.error = d.get("error")
        dl.total_bytes = d.get("total_bytes", 0)
        dl.downloaded_bytes = d.get("downloaded_bytes", 0)
        if dl.status == "downloading":
            dl.status = "pending"
        return dl


class DownloadManager:
    def __init__(self, history=None):
        self.queue = []
        self.current = None
        self._thread = None
        self._cancel = False
        self._lock = threading.Lock()
        self.history = history

    def check_disk_space(self, dest_path, needed=0):
        try:
            os.makedirs(dest_path, exist_ok=True)
            usage = shutil.disk_usage(dest_path)
            if needed > 0 and usage.free < needed:
                return False, usage.free
            return True, usage.free
        except OSError:
            return True, 0

    def add(self, url, dest_path, filename):
        dl = Download(url, dest_path, filename)
        with self._lock:
            self.queue.append(dl)
        self._start_next()
        return dl

    def cancel(self, dl):
        if dl.status == "downloading":
            self._cancel = True
        elif dl.status == "pending":
            dl.status = "cancelled"

    def retry(self, dl):
        if dl.status in ("error", "cancelled"):
            dl.status = "pending"
            dl.progress = 0.0
            dl.downloaded_bytes = 0
            dl.speed = 0
            dl.error = None
            self._start_next()

    def remove(self, dl):
        if dl.status == "downloading":
            self._cancel = True
        with self._lock:
            if dl in self.queue:
                self.queue.remove(dl)

    def retry_all_failed(self):
        retried = 0
        with self._lock:
            for dl in self.queue:
                if dl.status == "error":
                    dl.status = "pending"
                    dl.progress = 0.0
                    dl.downloaded_bytes = 0
                    dl.speed = 0
                    dl.error = None
                    retried += 1
        if retried:
            self._start_next()
        return retried

    def remove_completed(self):
        with self._lock:
            self.queue = [d for d in self.queue if d.status not in ("done", "error", "cancelled")]

    def get_all(self):
        with self._lock:
            return list(self.queue)

    def save_queue(self):
        with self._lock:
            data = [dl.to_dict() for dl in self.queue if dl.status in ("pending", "downloading")]
        try:
            with open(QUEUE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def is_bg_running(self):
        if not os.path.exists(BG_PID_FILE):
            return False
        try:
            with open(BG_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            try:
                os.remove(BG_PID_FILE)
            except OSError:
                pass
            return False

    def load_queue(self):
        if not os.path.exists(QUEUE_FILE):
            return
        bg_running = self.is_bg_running()
        try:
            with open(QUEUE_FILE, "r") as f:
                data = json.load(f)
            for d in data:
                dl = Download.from_dict(d)
                filepath = os.path.join(dl.dest_path, dl.filename)
                if dl.status == "done":
                    pass
                elif dl.status == "error":
                    pass
                elif os.path.exists(filepath):
                    dl.status = "done"
                    dl.error = "Downloaded in background"
                elif bg_running:
                    dl.status = "downloading"
                    dl.error = "Background download"
                else:
                    dl.status = "pending"
                    dl.error = None
                with self._lock:
                    exists = any(q.url == dl.url for q in self.queue)
                    if not exists:
                        self.queue.append(dl)
            if not bg_running:
                try:
                    os.remove(QUEUE_FILE)
                except OSError:
                    pass
                self._start_next()
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    def refresh_bg_status(self):
        if not self.is_bg_running():
            with self._lock:
                for dl in self.queue:
                    if dl.error == "Background download":
                        filepath = os.path.join(dl.dest_path, dl.filename)
                        if os.path.exists(filepath):
                            dl.status = "done"
                            dl.error = "Downloaded in background"
                        else:
                            dl.status = "pending"
                            dl.error = None
            if os.path.exists(QUEUE_FILE):
                self.load_queue()
            return False
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r") as f:
                    data = json.load(f)
                status_map = {d["url"]: d for d in data}
                with self._lock:
                    for dl in self.queue:
                        if dl.url in status_map:
                            info = status_map[dl.url]
                            filepath = os.path.join(dl.dest_path, dl.filename)
                            if info["status"] == "done" or os.path.exists(filepath):
                                dl.status = "done"
                                dl.error = "Downloaded in background"
                            elif info["status"] == "error":
                                dl.status = "error"
                                dl.error = info.get("error", "Failed in background")
                            elif info["status"] == "downloading":
                                dl.status = "downloading"
                                dl.error = "Background download"
                                dl.downloaded_bytes = info.get("downloaded_bytes", 0)
                                dl.total_bytes = info.get("total_bytes", 0)
                                if dl.total_bytes > 0:
                                    dl.progress = dl.downloaded_bytes / dl.total_bytes
            except (json.JSONDecodeError, OSError):
                pass
        return True

    def has_active(self):
        with self._lock:
            return any(d.status in ("pending", "downloading") and d.error != "Background download" for d in self.queue)

    def spawn_background(self):
        if self.is_bg_running():
            self.save_queue()
            return
        self.save_queue()
        has_pending = False
        with self._lock:
            has_pending = any(d.status in ("pending",) for d in self.queue)
        if not has_pending:
            return
        app_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(app_dir, "bg_download.py")
        log = os.path.join(app_dir, "bg.log")
        if not os.path.exists(script):
            return
        try:
            log_fd = open(log, "a")
            subprocess.Popen(
                ["nohup", "python3", script],
                stdout=log_fd,
                stderr=log_fd,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                cwd=app_dir,
                close_fds=True,
            )
            log_fd.close()
        except Exception:
            pass

    def stop_background(self):
        if not os.path.exists(BG_PID_FILE):
            return
        try:
            with open(BG_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)
        except (OSError, ValueError):
            pass
        finally:
            try:
                os.remove(BG_PID_FILE)
            except OSError:
                pass

    def _start_next(self):
        with self._lock:
            if self._thread and self._thread.is_alive() and self._thread != threading.current_thread():
                return
            pending = [d for d in self.queue if d.status == "pending"]
            if not pending:
                self.current = None
                return
            self.current = pending[0]
        self._cancel = False
        self._thread = threading.Thread(target=self._run_worker, daemon=True)
        self._thread.start()

    def _run_worker(self):
        self._download_worker()
        self._start_next()

    SEGMENTS = 4
    CHUNK_SIZE = 256 * 1024
    MIN_SEGMENT_SIZE = 512 * 1024

    def _make_headers(self):
        headers = {
            "User-Agent": ArchiveAPI.USER_AGENT,
            "Referer": "https://archive.org/",
            "Accept": "*/*",
        }
        cookies = get_auth_cookies()
        if cookies:
            headers["Cookie"] = cookies
        return headers

    def _get_file_info(self, url):
        headers = self._make_headers()
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            size = int(resp.headers.get("Content-Length", 0))
            accept_ranges = resp.headers.get("Accept-Ranges", "")
            return size, "bytes" in accept_ranges.lower()

    def _download_segment(self, url, start, end, part_path, dl, seg_progress, seg_idx):
        headers = self._make_headers()
        headers["Range"] = f"bytes={start}-{end}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(part_path, "wb") as f:
                while True:
                    if self._cancel:
                        return False
                    chunk = resp.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    seg_progress[seg_idx] += len(chunk)
        return True

    def _download_worker(self):
        dl = self.current
        dl.status = "downloading"
        dl.start_time = time.time()
        safe_name = dl.filename.replace("\\", "/").split("/")[-1]
        dl.filename = safe_name
        os.makedirs(dl.dest_path, exist_ok=True)
        filepath = os.path.join(dl.dest_path, safe_name)

        max_retries = 3
        for attempt in range(max_retries):
            if self._cancel:
                dl.status = "cancelled"
                break
            dl.downloaded_bytes = 0
            dl.progress = 0.0
            dl.speed = 0
            dl.error = None
            try:
                file_size, supports_range = self._get_file_info(dl.url)
                dl.total_bytes = file_size

                use_multi = supports_range and file_size >= self.MIN_SEGMENT_SIZE * 2
                if use_multi:
                    self._download_multi(dl, filepath, file_size)
                else:
                    self._download_single(dl, filepath)

                if dl.status == "downloading":
                    dl.progress = 1.0
                    dl.status = "done"
                    self._extract_if_archive(dl, filepath)
                    if self.history:
                        self.history.add(dl.filename, dl.url, dl.dest_path, dl.total_bytes)
                break
            except urllib.error.HTTPError as e:
                self._cleanup_file(filepath)
                if e.code == 403:
                    dl.error = "Login required on archive.org"
                    dl.status = "error"
                    break
                elif e.code == 404:
                    dl.error = "File not found"
                    dl.status = "error"
                    break
                elif attempt < max_retries - 1:
                    dl.error = f"Retry {attempt + 2}/{max_retries}..."
                    time.sleep(2)
                else:
                    dl.error = f"HTTP {e.code}: {e.reason}"
                    dl.status = "error"
            except Exception as e:
                self._cleanup_file(filepath)
                if attempt < max_retries - 1:
                    dl.error = f"Retry {attempt + 2}/{max_retries}..."
                    time.sleep(2)
                else:
                    dl.error = str(e)
                    dl.status = "error"

    def _cleanup_file(self, filepath):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    def _download_single(self, dl, filepath):
        headers = self._make_headers()
        req = urllib.request.Request(dl.url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            dl.total_bytes = int(resp.headers.get("Content-Length", 0))
            start_time = time.time()
            with open(filepath, "wb") as f:
                while True:
                    if self._cancel:
                        dl.status = "cancelled"
                        return
                    chunk = resp.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    dl.downloaded_bytes += len(chunk)
                    if dl.total_bytes > 0:
                        dl.progress = dl.downloaded_bytes / dl.total_bytes
                    elapsed = time.time() - start_time
                    if elapsed > 0:
                        dl.speed = dl.downloaded_bytes / elapsed

    def _download_multi(self, dl, filepath, file_size):
        seg_count = min(self.SEGMENTS, max(1, file_size // self.MIN_SEGMENT_SIZE))
        seg_size = file_size // seg_count
        segments = []
        for i in range(seg_count):
            start = i * seg_size
            end = file_size - 1 if i == seg_count - 1 else (i + 1) * seg_size - 1
            part_path = filepath + f".part{i}"
            segments.append((start, end, part_path))

        seg_progress = [0] * seg_count
        errors = [None] * seg_count
        start_time = time.time()

        def run_seg(idx, start, end, part_path):
            try:
                self._download_segment(dl.url, start, end, part_path, dl, seg_progress, idx)
            except Exception as e:
                errors[idx] = e

        threads = []
        for i, (start, end, part_path) in enumerate(segments):
            t = threading.Thread(target=run_seg, args=(i, start, end, part_path), daemon=True)
            threads.append(t)
            t.start()

        while any(t.is_alive() for t in threads):
            time.sleep(0.2)
            dl.downloaded_bytes = sum(seg_progress)
            if file_size > 0:
                dl.progress = dl.downloaded_bytes / file_size
            elapsed = time.time() - start_time
            if elapsed > 0:
                dl.speed = dl.downloaded_bytes / elapsed
            if self._cancel:
                break

        for t in threads:
            t.join(timeout=2)

        if self._cancel:
            dl.status = "cancelled"
            for _, _, part_path in segments:
                self._cleanup_file(part_path)
            return

        for e in errors:
            if e is not None:
                for _, _, part_path in segments:
                    self._cleanup_file(part_path)
                raise e

        with open(filepath, "wb") as out:
            for _, _, part_path in segments:
                with open(part_path, "rb") as part:
                    while True:
                        chunk = part.read(self.CHUNK_SIZE)
                        if not chunk:
                            break
                        out.write(chunk)
                os.remove(part_path)

        dl.downloaded_bytes = file_size
        dl.progress = 1.0

    ARCHIVE_EXTS = (".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".tar.gz", ".tgz")

    def _extract_if_archive(self, dl, filepath):
        lower = filepath.lower()
        if not any(lower.endswith(ext) for ext in self.ARCHIVE_EXTS):
            return
        dl.status = "extracting"
        dl.error = None
        if self._extract_with_7z(dl, filepath):
            return
        if lower.endswith(".zip"):
            self._extract_with_python(dl, filepath)

    def _extract_with_7z(self, dl, filepath):
        for cmd in ("7z", "7za", "7zr"):
            try:
                result = subprocess.run(
                    [cmd, "x", "-y", f"-o{dl.dest_path}", filepath],
                    capture_output=True, timeout=600,
                )
                if result.returncode == 0:
                    os.remove(filepath)
                    dl.status = "done"
                    return True
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                dl.error = "Extract timed out"
                dl.status = "done"
                return True
            except Exception as e:
                dl.error = f"Extract failed: {e}"
                dl.status = "done"
                return True
        return False

    def _extract_with_python(self, dl, filepath):
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                zf.extractall(dl.dest_path)
            os.remove(filepath)
            dl.status = "done"
        except zipfile.BadZipFile:
            dl.status = "done"
        except Exception as e:
            dl.error = f"Extract failed: {e}"
            dl.status = "done"


HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")


class DownloadHistory:
    def __init__(self):
        self.entries = []
        self._load()

    def _load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.entries = []

    def _save(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.entries, f, indent=2)
        except OSError:
            pass

    def add(self, filename, url, dest_path, size):
        for e in self.entries:
            if e["url"] == url:
                e["filename"] = filename
                e["dest_path"] = dest_path
                e["size"] = size
                self._save()
                return
        self.entries.insert(0, {
            "filename": filename,
            "url": url,
            "dest_path": dest_path,
            "size": size,
        })
        if len(self.entries) > 200:
            self.entries = self.entries[:200]
        self._save()

    def remove(self, entry):
        self.entries = [e for e in self.entries if e["url"] != entry["url"]]
        self._save()

    def clear(self):
        self.entries = []
        self._save()

    def get_all(self):
        return list(self.entries)

    def is_on_disk(self, entry):
        path = os.path.join(entry["dest_path"], entry["filename"])
        return os.path.exists(path)


class AsyncTask:
    def __init__(self, func, *args, **kwargs):
        self.result = None
        self.error = None
        self.done = False
        self._thread = threading.Thread(
            target=self._run, args=(func, args, kwargs), daemon=True
        )
        self._thread.start()

    def _run(self, func, args, kwargs):
        try:
            self.result = func(*args, **kwargs)
        except Exception as e:
            self.error = str(e)
        self.done = True
