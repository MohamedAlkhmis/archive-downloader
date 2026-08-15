import os
import json
import platform

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 30
FPS_IDLE = 5

COLORS = {
    "bg": (15, 15, 26),
    "bg_light": (25, 25, 50),
    "bg_lighter": (35, 35, 65),
    "header": (18, 18, 38),
    "accent": (74, 158, 255),
    "accent_dark": (35, 55, 100),
    "accent_glow": (100, 180, 255),
    "text": (240, 240, 255),
    "text_dim": (120, 120, 160),
    "text_hint": (80, 80, 110),
    "success": (74, 220, 130),
    "error": (255, 80, 80),
    "warning": (255, 200, 60),
    "divider": (40, 40, 70),
    "scrollbar": (60, 60, 100),
    "scrollbar_thumb": (100, 100, 160),
}

FONT_SIZE_TITLE = 22
FONT_SIZE_BODY = 17
FONT_SIZE_SMALL = 14
FONT_SIZE_HINT = 12

HEADER_HEIGHT = 42
FOOTER_HEIGHT = 36
CONTENT_Y = HEADER_HEIGHT
CONTENT_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT

IS_DEVICE = platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
ROM_BASE_PATH = "/userdata/roms" if IS_DEVICE else os.path.join(os.path.dirname(__file__), "downloads")
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

ALL_SYSTEMS = [
    {"name": "Game Boy Advance", "dir": "gba", "tag": "GBA", "query": "gameboy advance roms", "default": True},
    {"name": "Game Boy Color", "dir": "gbc", "tag": "GBC", "query": "gameboy color roms", "default": True},
    {"name": "Game Boy", "dir": "gb", "tag": "GB", "query": "gameboy roms", "default": True},
    {"name": "Super Nintendo", "dir": "snes", "tag": "SNES", "query": "super nintendo snes roms", "default": True},
    {"name": "NES", "dir": "nes", "tag": "NES", "query": "nintendo nes roms", "default": True},
    {"name": "Nintendo 64", "dir": "n64", "tag": "N64", "query": "nintendo 64 roms", "default": True},
    {"name": "Nintendo DS", "dir": "nds", "tag": "NDS", "query": "nintendo ds roms", "default": True},
    {"name": "PlayStation", "dir": "psx", "tag": "PSX", "query": "playstation psx roms", "default": True},
    {"name": "PlayStation 2", "dir": "ps2", "tag": "PS2", "query": "playstation 2 ps2 isos", "default": False},
    {"name": "PSP", "dir": "psp", "tag": "PSP", "query": "psp iso roms", "default": False},
    {"name": "Sega Genesis", "dir": "megadrive", "tag": "GEN", "query": "sega genesis megadrive roms", "default": True},
    {"name": "Sega Master System", "dir": "mastersystem", "tag": "SMS", "query": "sega master system roms", "default": True},
    {"name": "Sega CD", "dir": "segacd", "tag": "SCD", "query": "sega cd roms iso", "default": False},
    {"name": "Sega 32X", "dir": "sega32x", "tag": "32X", "query": "sega 32x roms", "default": False},
    {"name": "Sega Saturn", "dir": "saturn", "tag": "SAT", "query": "sega saturn roms iso", "default": False},
    {"name": "Dreamcast", "dir": "dreamcast", "tag": "DC", "query": "dreamcast roms iso", "default": False},
    {"name": "Game Gear", "dir": "gamegear", "tag": "GG", "query": "sega game gear roms", "default": True},
    {"name": "PC Engine", "dir": "pcengine", "tag": "PCE", "query": "pc engine turbografx roms", "default": True},
    {"name": "PC Engine CD", "dir": "pcenginecd", "tag": "PCD", "query": "pc engine cd turbografx cd roms", "default": False},
    {"name": "Neo Geo", "dir": "neogeo", "tag": "NG", "query": "neo geo roms", "default": False},
    {"name": "Neo Geo Pocket", "dir": "ngp", "tag": "NGP", "query": "neo geo pocket roms", "default": False},
    {"name": "Neo Geo CD", "dir": "neogeocd", "tag": "NCD", "query": "neo geo cd roms iso", "default": False},
    {"name": "Atari 2600", "dir": "atari2600", "tag": "A26", "query": "atari 2600 roms", "default": False},
    {"name": "Atari 5200", "dir": "atari5200", "tag": "A52", "query": "atari 5200 roms", "default": False},
    {"name": "Atari 7800", "dir": "atari7800", "tag": "A78", "query": "atari 7800 roms", "default": False},
    {"name": "Atari Jaguar", "dir": "jaguar", "tag": "JAG", "query": "atari jaguar roms", "default": False},
    {"name": "Atari Lynx", "dir": "lynx", "tag": "LNX", "query": "atari lynx roms", "default": False},
    {"name": "Wonderswan", "dir": "wonderswan", "tag": "WS", "query": "wonderswan roms", "default": False},
    {"name": "ColecoVision", "dir": "coleco", "tag": "COL", "query": "colecovision roms", "default": False},
    {"name": "Intellivision", "dir": "intellivision", "tag": "INT", "query": "intellivision roms", "default": False},
    {"name": "Virtual Boy", "dir": "virtualboy", "tag": "VB", "query": "virtual boy roms", "default": False},
    {"name": "3DO", "dir": "3do", "tag": "3DO", "query": "3do roms iso", "default": False},
    {"name": "Vectrex", "dir": "vectrex", "tag": "VEC", "query": "vectrex roms", "default": False},
    {"name": "Arcade / MAME", "dir": "mame", "tag": "ARC", "query": "mame arcade roms", "default": True},
]

ROM_EXTENSIONS = {
    ".zip", ".7z", ".rar",
    ".gba", ".gbc", ".gb", ".sgb",
    ".sfc", ".smc", ".nes", ".unf", ".fds",
    ".md", ".smd", ".gen", ".bin", ".iso", ".cue",
    ".n64", ".z64", ".v64", ".nds",
    ".pce", ".ngp", ".ngc", ".gg", ".sms",
    ".a26", ".a78", ".ws", ".wsc", ".lnx",
    ".pbp", ".chd", ".cso", ".img", ".mdf",
    ".col", ".sg", ".32x",
    ".nrg", ".cdi", ".gdi",
}

EXT_TO_SYSTEM = {
    ".gba": "gba",
    ".gbc": "gbc",
    ".gb": "gb", ".sgb": "gb",
    ".sfc": "snes", ".smc": "snes",
    ".nes": "nes", ".unf": "nes", ".fds": "nes",
    ".md": "megadrive", ".smd": "megadrive", ".gen": "megadrive",
    ".sms": "mastersystem",
    ".gg": "gamegear",
    ".pbp": "psx",
    ".n64": "n64", ".z64": "n64", ".v64": "n64",
    ".nds": "nds",
    ".pce": "pcengine",
    ".ngp": "ngp", ".ngc": "ngp",
    ".a26": "atari2600",
    ".a78": "atari7800",
    ".ws": "wonderswan", ".wsc": "wonderswan",
    ".lnx": "lynx",
    ".col": "coleco",
    ".gdi": "dreamcast",
    ".vb": "virtualboy",
}


def detect_system_dir(filename, fallback=None):
    ext = os.path.splitext(filename)[1].lower()
    return EXT_TO_SYSTEM.get(ext, fallback)


GAMEPAD_CONFIRM = [3]
GAMEPAD_BACK = [4]
GAMEPAD_START = [10]
GAMEPAD_SELECT = [9]
GAMEPAD_L = [7]
GAMEPAD_R = [8]


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass


def get_enabled_systems():
    settings = load_settings()
    enabled = settings.get("enabled_systems", None)
    if enabled is None:
        return [s for s in ALL_SYSTEMS if s.get("default")]
    return [s for s in ALL_SYSTEMS if s["dir"] in enabled]


def set_enabled_systems(dirs):
    settings = load_settings()
    settings["enabled_systems"] = dirs
    save_settings(settings)


def get_custom_paths():
    settings = load_settings()
    return settings.get("custom_paths", {})


def set_custom_path(system_dir, path):
    settings = load_settings()
    if "custom_paths" not in settings:
        settings["custom_paths"] = {}
    settings["custom_paths"][system_dir] = path
    save_settings(settings)


def reset_custom_path(system_dir):
    settings = load_settings()
    if "custom_paths" in settings and system_dir in settings["custom_paths"]:
        del settings["custom_paths"][system_dir]
        save_settings(settings)


def reset_all_paths():
    settings = load_settings()
    settings.pop("custom_paths", None)
    save_settings(settings)


def get_bg_download_enabled():
    settings = load_settings()
    return settings.get("bg_download", True)


def set_bg_download_enabled(enabled):
    settings = load_settings()
    settings["bg_download"] = enabled
    save_settings(settings)


FAVORITES_FILE = os.path.join(CONFIG_DIR, "favorites.json")


def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_favorites(favorites):
    try:
        with open(FAVORITES_FILE, "w") as f:
            json.dump(favorites, f, indent=2)
    except OSError:
        pass


def add_favorite(identifier, title, system_dir=None):
    favs = load_favorites()
    for f in favs:
        if f["identifier"] == identifier:
            return False
    favs.insert(0, {"identifier": identifier, "title": title, "system_dir": system_dir})
    save_favorites(favs)
    return True


def remove_favorite(identifier):
    favs = load_favorites()
    favs = [f for f in favs if f["identifier"] != identifier]
    save_favorites(favs)


def is_favorite(identifier):
    favs = load_favorites()
    return any(f["identifier"] == identifier for f in favs)


def get_rom_path(system_dir):
    custom = get_custom_paths()
    if system_dir in custom:
        path = custom[system_dir]
    else:
        path = os.path.join(ROM_BASE_PATH, system_dir)
    os.makedirs(path, exist_ok=True)
    return path


def get_default_rom_path(system_dir):
    return os.path.join(ROM_BASE_PATH, system_dir)


def load_custom_collections():
    path = os.path.join(CONFIG_DIR, "collections.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_custom_collections(collections):
    path = os.path.join(CONFIG_DIR, "collections.json")
    with open(path, "w") as f:
        json.dump(collections, f, indent=2)


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024*1024):.1f} MB"
    else:
        return f"{size_bytes / (1024*1024*1024):.2f} GB"


def format_eta(seconds):
    if seconds < 0:
        return ""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    else:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m"
