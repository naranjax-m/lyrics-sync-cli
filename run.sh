#!/usr/bin/env bash
#
# run.sh — Activates the virtual environment and runs Lyrics Sync CLI.
#
# Usage:
#   ./run.sh                  # normal run
#   ./run.sh --interval 0.3   # any argument is passed through to main.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
fi

if ! command -v playerctl &> /dev/null; then
    echo "Warning: playerctl is not installed. Run ./install.sh first."
fi

source venv/bin/activate
python main.py "$@"
