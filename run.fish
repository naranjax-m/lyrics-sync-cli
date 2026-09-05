#!/usr/bin/env fish
#
# run.fish — Activates the virtual environment and runs Lyrics Sync CLI.
# Fish-shell equivalent of run.sh.
#
# Usage:
#   ./run.fish                  # normal run
#   ./run.fish --interval 0.3   # any argument is passed through to main.py
#   ./run.fish --ascii
#   ./run.fish --search "Artist Name - Song Title"
#   ./run.fish --install ~/Lyrics "Artist Name - Song Title"

set SCRIPT_DIR (dirname (status --current-filename))
cd $SCRIPT_DIR

if not test -d venv
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
end

if not command -v playerctl > /dev/null
    echo "Warning: playerctl is not installed. Run ./install.sh first."
end

source venv/bin/activate.fish
python main.py $argv
