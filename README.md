# Archive Downloader for Knulli

A ROM downloader for Anbernic RG35XX H (and similar handhelds) running Knulli/Batocera. Browse and search archive.org, download ROMs directly to the device, and manage downloads — all from a gamepad-friendly GUI.

![SDL GUI · 640×480](https://img.shields.io/badge/SDL_GUI-640x480-blue)
![Python 3](https://img.shields.io/badge/Python-3-green)
![Knulli / Batocera](https://img.shields.io/badge/Knulli-Batocera-orange)

## Features

- Browse ROMs by system (34 systems from Game Boy to PS2)
- Enable/disable systems from settings — only show what you need
- Free-text search across all of archive.org
- Paginated results with load-more
- Multi-connection downloads (4 parallel segments) with progress bar and speed display
- Background downloads — keep downloading after exiting the app, play games while waiting
- Background download indicator in the app header (blinking BG icon)
- Toggle background downloads on/off from Settings
- Auto-extracts archives after download (ZIP, 7z, RAR, TAR, GZ)
- Smart file routing — downloads go to the correct system folder based on file extension
- Per-system custom download paths
- Archive.org login support for restricted collections
- Download history with redownload support
- On-screen keyboard with lowercase, uppercase, and symbols pages
- Quick-insert buttons (.com, @gmail.com) on the keyboard
- Gamepad and keyboard input
- SELECT+START to quit

## Supported Systems

**Enabled by default:** GBA, GBC, Game Boy, SNES, NES, N64, NDS, PlayStation, Genesis, Master System, Game Gear, PC Engine, Arcade/MAME

**Available in settings:** PS2, PSP, Dreamcast, Saturn, Sega CD, Sega 32X, PC Engine CD, Neo Geo, Neo Geo Pocket, Neo Geo CD, Atari 2600, Atari 5200, Atari 7800, Atari Jaguar, Atari Lynx, Wonderswan, ColecoVision, Intellivision, Virtual Boy, 3DO, Vectrex

## Installation

### On Device (Knulli / Batocera)

1. Copy the `archive-downloader` folder to:
   ```
   /userdata/roms/ports/archive-downloader/
   ```

2. Refresh your game list in Knulli — the app appears as **Archive Downloader** under **Ports**.

### On PC (for development)

```bash
pip install pygame
python main.py
```

ROMs download to a `downloads/` subfolder when running on PC.

## Controls

| Action | Gamepad | Keyboard |
|--------|---------|----------|
| Navigate | D-Pad | Arrow Keys |
| Select / Confirm | A | Enter / Space |
| Back | B | Escape / Backspace |
| Switch Tab / Page | L1 / R1 | Page Up / Page Down |
| Menu Action | Start | Tab |
| Quit App | Select + Start | — |

## Settings

- **Archive.org Account** — Log in to access restricted collections
- **Background Downloads** — Toggle on/off; when on, downloads continue after exiting the app
- **Manage Systems** — Toggle which systems appear in Browse (A to toggle, START for all/none)
- **System Paths** — Set custom download paths per system (START to reset)

## File Structure

```
archive-downloader/
├── main.py                  # Entry point
├── config.py                # Screen, colors, system definitions, paths
├── archive_api.py           # Archive.org API, downloads, auth, history
├── bg_download.py           # Background download process
├── ui.py                    # All GUI screens and components
├── Archive Downloader.sh    # Knulli/Batocera launcher
├── Archive Downloader.png   # App icon for Knulli
├── gamelist.xml             # EmulationStation metadata for app icon
├── collections.json         # Custom collection config
└── requirements.txt         # Python dependencies
```

**Auto-generated files** (not included in repo):
- `settings.json` — Enabled systems, custom paths, background download toggle
- `credentials.json` — Archive.org login cookies
- `history.json` — Download history
- `queue.json` — Active download queue (shared between app and background process)
- `bg.pid` — Background download process ID

## Archive.org Login

Some collections on archive.org require a free account. To log in:

1. Go to **Settings** from the main menu
2. Select **Archive.org Account**
3. Enter your email and password using the on-screen keyboard

Credentials are stored locally in `credentials.json`.

## Download History

Completed downloads are saved to `history.json`. Open **Downloads** and press **R** to switch to the **History** tab. Items show whether the file is still on the device — press **A** to redownload missing files.

## Smart File Routing

Downloads are automatically placed in the correct system folder based on file extension. For example, a `.gba` file always goes to the GBA folder regardless of which system you browsed from. Ambiguous formats (`.bin`, `.iso`, `.chd`) use the browsed system as the destination.

## License

MIT
