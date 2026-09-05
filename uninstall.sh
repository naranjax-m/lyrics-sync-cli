#!/usr/bin/env bash
#
# uninstall.sh — Removes the virtual environment created by install.sh.
# (playerctl is not removed automatically in case you use it elsewhere)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    echo "==> Removing virtual environment..."
    rm -rf venv
    echo "==> Done."
else
    echo "No virtual environment to remove."
fi

echo ""
echo "If you also want to remove playerctl:"
echo "  sudo pacman -Rns playerctl"
