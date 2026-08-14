import os
import json
import platform

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 30

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
CONFIG_DIR = os.path.dirname(__file__)

ARCHIVE_SEARCH_URL = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA_URL = "https://archive.org/metadata/{}"
ARCHIVE_DOWNLOAD_URL = "https://archive.org/download/{}/{}"

SYSTEMS = [
    {"name": "Game Boy Advance", "dir": "gba", "tag": "GBA", "query": "gameboy advance roms"},
    {"name": "Game Boy Color", "dir": "gbc", "tag": "GBC", "query": "gameboy color roms"},
    {"name": "Game Boy", "dir": "gb", "tag": "GB", "query": "gameboy roms"},
    {"name": "Super Nintendo", "dir": "snes", "tag": "SNES", "query": "super nintendo snes roms"},
    {"name": "NES", "dir": "nes", "tag": "NES", "query": "nintendo nes roms"},
    {"name": "Sega Genesis", "dir": "megadrive", "tag": "GEN", "query": "sega genesis megadrive roms"},
    {"name": "Sega Master System", "dir": "mastersystem", "tag": "SMS", "query": "sega master system roms"},
    {"name": "PlayStation", "dir": "psx", "tag": "PSX", "query": "playstation psx roms"},
    {"name": "Nintendo 64", "dir": "n64", "tag": "N64", "query": "nintendo 64 roms"},
    {"name": "Nintendo DS", "dir": "nds", "tag": "NDS", "query": "nintendo ds roms"},
    {"name": "PC Engine", "dir": "pcengine", "tag": "PCE", "query": "pc engine turbografx roms"},
    {"name": "Neo Geo Pocket", "dir": "ngp", "tag": "NGP", "query": "neo geo pocket roms"},
    {"name": "Game Gear", "dir": "gamegear", "tag": "GG", "query": "sega game gear roms"},
    {"name": "Atari 2600", "dir": "atari2600", "tag": "A26", "query": "atari 2600 roms"},
    {"name": "Atari 7800", "dir": "atari7800", "tag": "A78", "query": "atari 7800 roms"},
    {"name": "Wonderswan", "dir": "wonderswan", "tag": "WS", "query": "wonderswan roms"},
    {"name": "Atari Lynx", "dir": "lynx", "tag": "LNX", "query": "atari lynx roms"},
    {"name": "Arcade / MAME", "dir": "mame", "tag": "ARC", "query": "mame arcade roms"},
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
}

GAMEPAD_CONFIRM = [0, 1]
GAMEPAD_BACK = [1, 0]
GAMEPAD_START = [7, 11]
GAMEPAD_SELECT = [6, 10]
GAMEPAD_L = [4, 9]
GAMEPAD_R = [5, 8]


def get_rom_path(system_dir):
    path = os.path.join(ROM_BASE_PATH, system_dir)
    os.makedirs(path, exist_ok=True)
    return path


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
