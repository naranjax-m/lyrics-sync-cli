"""
Linux backend: uses MPRIS (Media Player Remote Interfacing Specification)
through the `playerctl` command. MPRIS is a D-Bus standard that Spotify
(official app), modern browsers (Chrome, Firefox, Edge) and most media
players expose automatically. Since YouTube, YouTube Music and Apple
Music (web) use the browser's Media Session API, that gets translated
to MPRIS automatically: no need to integrate with each service and no
token required.

System requirement (not a Python package): `playerctl`
    Debian/Ubuntu: sudo apt install playerctl
    Arch:          sudo pacman -S playerctl
    Fedora:        sudo dnf install playerctl
"""

import shutil
import subprocess
from typing import Optional

from . import NowPlaying, NowPlayingBackend

_FORMAT = "{{status}}||{{artist}}||{{title}}||{{album}}||{{mpris:length}}||{{playerName}}"


class LinuxMPRISBackend(NowPlayingBackend):
    def is_available(self) -> bool:
        return shutil.which("playerctl") is not None

    def get_current(self) -> Optional[NowPlaying]:
        if not self.is_available():
            return None
        try:
            # General metadata
            meta = subprocess.run(
                ["playerctl", "metadata", "--format", _FORMAT],
                capture_output=True, text=True, timeout=2,
            )
            if meta.returncode != 0 or not meta.stdout.strip():
                return None
            status, artist, title, album, length_us, player = (
                meta.stdout.strip().split("||")
            )

            position = subprocess.run(
                ["playerctl", "position"],
                capture_output=True, text=True, timeout=2,
            )
            pos_seconds = float(position.stdout.strip() or 0.0)

            duration_seconds = 0.0
            if length_us and length_us.isdigit():
                duration_seconds = int(length_us) / 1_000_000.0

            if not title:
                return None

            return NowPlaying(
                title=title,
                artist=artist,
                album=album,
                position=pos_seconds,
                duration=duration_seconds,
                is_playing=(status.strip().lower() == "playing"),
                app=player.strip(),
            )
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            return None
