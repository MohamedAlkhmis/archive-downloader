# Archive Downloader for Knulli

A ROM downloader for Anbernic RG35XX H (and similar handhelds) running Knulli/Batocera. Browse and search archive.org, download ROMs directly to the device, and manage downloads — all from a gamepad-friendly GUI.

![SDL GUI · 640×480](https://img.shields.io/badge/SDL_GUI-640x480-blue)
![Python 3](https://img.shields.io/badge/Python-3-green)
![Knulli / Batocera](https://img.shields.io/badge/Knulli-Batocera-orange)

## Features

- Browse ROMs by system (18 consoles: GBA, SNES, PS1, Genesis, and more)
- Free-text search across all of archive.org
- Paginated results with load-more
- Threaded downloads with progress bar and speed display
- Auto-extracts ZIP files after download
- Archive.org login support for restricted collections
- Download history with redownload support
- On-screen keyboard with letters and symbols
- Gamepad and keyboard input

## Supported Systems

GBA, GBC, Game Boy, NES, SNES, Genesis, Game Gear, Master System, Neo Geo Pocket, Atari 2600, Atari 7800, PS1, N64, Nintendo DS, TurboGrafx-16, Wonderswan, ColecoVision, Intellivision

## Installation

### On Device (Knulli / Batocera)

1. Copy the `archive-downloader` folder to:
   ```
   /userdata/roms/ports/archive-downloader/
   ```

2. Make the launch script executable:
   ```bash
   chmod +x /userdata/roms/ports/archive-downloader/launch.sh
   ```

3. Refresh your game list in Knulli — the app appears under **Ports**.

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
| Switch Tab / Page | L / R | Page Up / Page Down |
| Clear / Menu | Start | Tab |

## File Structure

```
archive-downloader/
├── main.py            # Entry point
├── config.py          # Screen, colors, system definitions, paths
├── archive_api.py     # Archive.org API, downloads, auth, history
├── ui.py              # All GUI screens and components
├── launch.sh          # Knulli/Batocera launcher
├── collections.json   # Custom collection config
└── requirements.txt   # Python dependencies
```

## Archive.org Login

Some collections on archive.org require a free account. To log in:

1. Go to **Settings** from the main menu
2. Select **Archive.org Account**
3. Enter your email and password using the on-screen keyboard

Credentials are stored locally in `credentials.json`.

## Download History

Completed downloads are saved to `history.json`. Open **Downloads** and press **R** to switch to the **History** tab. Items show whether the file is still on the device — press **A** to redownload missing files.

## License

MIT
