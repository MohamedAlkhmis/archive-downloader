import json
import os
import sys
import signal
import threading
import time
import urllib.request
import urllib.parse
import zipfile
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

QUEUE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.json")
BG_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.pid")
USER_AGENT = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
SEGMENTS = 4
CHUNK_SIZE = 256 * 1024
MIN_SEGMENT_SIZE = 512 * 1024

running = True


def signal_handler(sig, frame):
    global running
    running = False


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def get_auth_cookies():
    from archive_api import load_credentials
    creds = load_credentials()
    if creds and creds.get("logged_in_user") and creds.get("logged_in_sig"):
        return f"logged-in-user={creds['logged_in_user']}; logged-in-sig={creds['logged_in_sig']}"
    return None


def make_headers():
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://archive.org/",
        "Accept": "*/*",
    }
    cookies = get_auth_cookies()
    if cookies:
        headers["Cookie"] = cookies
    return headers


def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_queue(queue):
    try:
        with open(QUEUE_FILE, "w") as f:
            json.dump(queue, f, indent=2)
    except OSError:
        pass


def save_to_history(item):
    from archive_api import DownloadHistory
    history = DownloadHistory()
    history.add(item["filename"], item["url"], item["dest_path"], item.get("total_bytes", 0))


def download_segment(url, start, end, part_path, progress, idx):
    headers = make_headers()
    headers["Range"] = f"bytes={start}-{end}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(part_path, "wb") as f:
            while running:
                chunk = resp.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                progress[idx] += len(chunk)


def download_file(item, queue):
    url = item["url"]
    dest_path = item["dest_path"]
    filename = item["filename"].replace("\\", "/").split("/")[-1]
    item["filename"] = filename
    os.makedirs(dest_path, exist_ok=True)
    filepath = os.path.join(dest_path, filename)
    last_save = [time.time()]

    def save_progress():
        now = time.time()
        if now - last_save[0] >= 2:
            last_save[0] = now
            save_queue(queue)

    try:
        headers = make_headers()
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            file_size = int(resp.headers.get("Content-Length", 0))
            accept_ranges = "bytes" in resp.headers.get("Accept-Ranges", "").lower()

        item["total_bytes"] = file_size
        use_multi = accept_ranges and file_size >= MIN_SEGMENT_SIZE * 2

        if use_multi:
            seg_count = min(SEGMENTS, max(1, file_size // MIN_SEGMENT_SIZE))
            seg_size = file_size // seg_count
            segments = []
            for i in range(seg_count):
                start = i * seg_size
                end = file_size - 1 if i == seg_count - 1 else (i + 1) * seg_size - 1
                segments.append((start, end, filepath + f".part{i}"))

            progress = [0] * seg_count
            errors = [None] * seg_count

            def run_seg(idx, start, end, part_path):
                try:
                    download_segment(url, start, end, part_path, progress, idx)
                except Exception as e:
                    errors[idx] = e

            threads = []
            for i, (start, end, part_path) in enumerate(segments):
                t = threading.Thread(target=run_seg, args=(i, start, end, part_path), daemon=True)
                threads.append(t)
                t.start()

            while any(t.is_alive() for t in threads):
                time.sleep(0.5)
                item["downloaded_bytes"] = sum(progress)
                save_progress()
                if not running:
                    break

            for t in threads:
                t.join(timeout=2)

            if not running:
                for _, _, pp in segments:
                    try:
                        os.remove(pp)
                    except OSError:
                        pass
                return False

            for e in errors:
                if e is not None:
                    for _, _, pp in segments:
                        try:
                            os.remove(pp)
                        except OSError:
                            pass
                    raise e

            with open(filepath, "wb") as out:
                for _, _, pp in segments:
                    with open(pp, "rb") as part:
                        while True:
                            chunk = part.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            out.write(chunk)
                    os.remove(pp)
        else:
            headers = make_headers()
            req = urllib.request.Request(url, headers=headers)
            downloaded = 0
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(filepath, "wb") as f:
                    while running:
                        chunk = resp.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        item["downloaded_bytes"] = downloaded
                        save_progress()

            if not running:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
                return False

        extract_archive(filepath, dest_path)
        item["status"] = "done"
        item["error"] = None
        item["downloaded_bytes"] = file_size
        save_to_history(item)
        return True

    except urllib.error.HTTPError as e:
        try:
            os.remove(filepath)
        except OSError:
            pass
        if e.code == 403:
            item["status"] = "error"
            item["error"] = "Login required"
        elif e.code == 404:
            item["status"] = "error"
            item["error"] = "File not found"
        else:
            item["status"] = "error"
            item["error"] = f"HTTP {e.code}"
        return True
    except Exception as e:
        try:
            os.remove(filepath)
        except OSError:
            pass
        item["status"] = "error"
        item["error"] = str(e)[:60]
        return True


def extract_archive(filepath, dest_path):
    lower = filepath.lower()
    archive_exts = (".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz", ".tgz")
    if not any(lower.endswith(ext) for ext in archive_exts):
        return
    for cmd in ("7z", "7za", "7zr"):
        try:
            result = subprocess.run(
                [cmd, "x", "-y", f"-o{dest_path}", filepath],
                capture_output=True, timeout=600,
            )
            if result.returncode == 0:
                os.remove(filepath)
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    if lower.endswith(".zip"):
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                zf.extractall(dest_path)
            os.remove(filepath)
        except Exception:
            pass


def write_pid():
    try:
        with open(BG_PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def main():
    write_pid()
    queue = load_queue()
    if not queue:
        cleanup()
        return

    for item in queue:
        if not running:
            break
        if item.get("status") not in ("pending", "downloading"):
            continue
        item["status"] = "downloading"
        save_queue(queue)
        download_file(item, queue)
        save_queue(queue)

    cleanup()


def cleanup():
    try:
        os.remove(BG_PID_FILE)
    except OSError:
        pass


if __name__ == "__main__":
    main()
