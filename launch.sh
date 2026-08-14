#!/bin/bash
# Launch script for Knulli / Batocera
# Place this folder in /userdata/roms/ports/ or run manually via SSH

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export SDL_VIDEODRIVER=kmsdrm
export SDL_AUDIODRIVER=dummy
export SDL_GAMECONTROLLERCONFIG=""

cd "$SCRIPT_DIR"
python3 main.py
