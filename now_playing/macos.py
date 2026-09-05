"""
macOS backend: uses Apple's private MediaRemote framework, the same
one that powers the "Now Playing" widget in Control Center. Access is
done through the open-source command-line utility `nowplaying-cli`,
which requires no token: it reads directly the state that any app
(Spotify, Music/Apple Music, Safari/Chrome playing YouTube or YouTube
Music) publishes to the system.

System requirement (not a Python package):
    brew install nowplaying-cli
    (repo: https://github.com/kirtan-shah/nowplaying-cli)
"""

import shutil
import subprocess
from typing import Optional

from . import NowPlaying, NowPlayingBackend

_KEYS = ["title", "artist", "album", "elapsedTime", "duration", "playing", "bundleIdentifier"]


class MacOSMediaRemoteBackend(NowPlayingBackend):
    def is_available(self) -> bool:
        return shutil.which("nowplaying-cli") is not None

    def get_current(self) -> Optional[NowPlaying]:
        if not self.is_available():
            return None
        try:
            values = {}
            for key in _KEYS:
                result = subprocess.run(
                    ["nowplaying-cli", "get", key],
                    capture_output=True, text=True, timeout=2,
                )
                values[key] = result.stdout.strip()

            title = values.get("title", "")
            if not title or title.lower() == "null":
                return None

            def to_float(s: str) -> float:
                try:
                    return float(s)
                except ValueError:
                    return 0.0

            return NowPlaying(
                title=title,
                artist=values.get("artist", ""),
                album=values.get("album", ""),
                position=to_float(values.get("elapsedTime", "0")),
                duration=to_float(values.get("duration", "0")),
                is_playing=values.get("playing", "").lower() in ("1", "true", "yes"),
                app=values.get("bundleIdentifier", ""),
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
