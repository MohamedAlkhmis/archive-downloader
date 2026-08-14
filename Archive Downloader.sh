#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$SCRIPT_DIR/crash.log"

export SDL_AUDIODRIVER=dummy
export SDL_GAMECONTROLLERCONFIG=""

cd "$SCRIPT_DIR"
python3 main.py >> "$LOG" 2>&1
