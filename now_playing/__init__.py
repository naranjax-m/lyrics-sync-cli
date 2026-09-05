"""
now_playing
-----------
Automatic detection of the currently playing track, using the "Now
Playing" APIs that the operating system itself exposes for ANY media
player (Spotify, a browser playing YouTube/YouTube Music/Apple Music,
native apps, etc). No service-specific API is used, so NO token, API
key, or login is required.

- Linux   -> MPRIS via D-Bus (playerctl)
- Windows -> GlobalSystemMediaTransportControlsSessionManager (GSMTC)
- macOS   -> MediaRemote framework (via the nowplaying-cli utility)
"""

import platform
from dataclasses import dataclass
from typing import Optional


@dataclass
class NowPlaying:
    title: str
    artist: str
    album: str = ""
    position: float = 0.0     # seconds
    duration: float = 0.0     # seconds
    is_playing: bool = True
    app: str = ""             # app/source name (Spotify, Chrome, etc.)


class NowPlayingBackend:
    """Common interface implemented by each platform backend."""

    def get_current(self) -> Optional[NowPlaying]:
        raise NotImplementedError

    def is_available(self) -> bool:
        raise NotImplementedError


def get_backend() -> NowPlayingBackend:
    system = platform.system()
    if system == "Linux":
        from .linux import LinuxMPRISBackend
        return LinuxMPRISBackend()
    elif system == "Windows":
        from .windows import WindowsGSMTCBackend
        return WindowsGSMTCBackend()
    elif system == "Darwin":
        from .macos import MacOSMediaRemoteBackend
        return MacOSMediaRemoteBackend()
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")
