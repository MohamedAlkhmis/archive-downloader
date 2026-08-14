#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTS_DIR="$(dirname "$SCRIPT_DIR")"
LOG="$SCRIPT_DIR/crash.log"

# Auto-install icon and gamelist on first run
if [ -f "$SCRIPT_DIR/images/Archive Downloader.png" ]; then
    mkdir -p "$PORTS_DIR/images"
    cp -n "$SCRIPT_DIR/images/Archive Downloader.png" "$PORTS_DIR/images/Archive Downloader.png" 2>/dev/null
fi
if [ -f "$SCRIPT_DIR/gamelist.xml" ] && ! grep -q "Archive Downloader" "$PORTS_DIR/gamelist.xml" 2>/dev/null; then
    if [ -f "$PORTS_DIR/gamelist.xml" ]; then
        sed -i '/<\/gameList>/d' "$PORTS_DIR/gamelist.xml"
        cat >> "$PORTS_DIR/gamelist.xml" <<'XMLEOF'
  <game>
    <path>./archive-downloader/Archive Downloader.sh</path>
    <name>Archive Downloader</name>
    <image>./images/Archive Downloader.png</image>
    <desc>Browse and download ROMs from archive.org</desc>
  </game>
</gameList>
XMLEOF
    else
        cp "$SCRIPT_DIR/gamelist.xml" "$PORTS_DIR/gamelist.xml"
    fi
fi

export SDL_AUDIODRIVER=dummy
export SDL_GAMECONTROLLERCONFIG=""

cd "$SCRIPT_DIR"
python3 main.py >> "$LOG" 2>&1
