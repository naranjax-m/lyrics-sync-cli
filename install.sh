#!/usr/bin/env bash
#
# install.sh — Installation for Arch Linux (and derivatives: Manjaro,
# EndeavourOS, etc.)
#
# Installs the system requirement (playerctl) and creates a Python
# virtual environment with the needed dependencies.

set -e

echo "==> Lyrics Sync CLI — installation for Arch Linux"

# 1. System dependency: playerctl (MPRIS/D-Bus detection)
if ! command -v playerctl &> /dev/null; then
    echo "==> Installing playerctl via pacman..."
    sudo pacman -S --needed --noconfirm playerctl
else
    echo "==> playerctl is already installed, skipping."
fi

# 2. Make sure python and pip are available
if ! command -v python3 &> /dev/null; then
    echo "==> Installing python..."
    sudo pacman -S --needed --noconfirm python python-pip
fi

# 3. Create virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "==> Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "==> Virtual environment already exists, skipping."
fi

echo "==> Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
deactivate

chmod +x run.sh

# 4. Create a "lyrics-sync" shell alias pointing at run.sh
ALIAS_LINE="alias lyrics-sync='$SCRIPT_DIR/run.sh'"

for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ]; then
        if ! grep -Fxq "$ALIAS_LINE" "$RC"; then
            echo "" >> "$RC"
            echo "# Added by install.sh (Lyrics Sync CLI)" >> "$RC"
            echo "$ALIAS_LINE" >> "$RC"
            echo "==> Added 'lyrics-sync' alias to $RC"
        else
            echo "==> 'lyrics-sync' alias already present in $RC, skipping."
        fi
    fi
done

echo ""
echo "==> Installation complete."
echo "==> Open a new terminal (or run 'source ~/.bashrc' / 'source ~/.zshrc')"
echo "    and then just run:  lyrics-sync"
echo "==> (You can still run it directly with:  ./run.sh)"
