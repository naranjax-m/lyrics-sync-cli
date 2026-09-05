"""
Windows backend: uses the GlobalSystemMediaTransportControlsSessionManager
(GSMTC), the same API that powers Windows 10/11's native "Now playing"
panel. Any app that integrates with the system's media controls shows
up here automatically: Spotify (desktop app), Chrome/Edge playing
YouTube, YouTube Music or Apple Music web, the Apple Music/iTunes app,
etc. No token required.

Python requirement:  pip install winsdk
"""

import asyncio
from typing import Optional

from . import NowPlaying, NowPlayingBackend

try:
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    _WINSDK_AVAILABLE = True
except ImportError:
    _WINSDK_AVAILABLE = False


class WindowsGSMTCBackend(NowPlayingBackend):
    def is_available(self) -> bool:
        return _WINSDK_AVAILABLE

    def get_current(self) -> Optional[NowPlaying]:
        if not _WINSDK_AVAILABLE:
            return None
        try:
            return asyncio.run(self._get_current_async())
        except Exception:
            return None

    async def _get_current_async(self) -> Optional[NowPlaying]:
        manager = await SessionManager.request_async()
        session = manager.get_current_session()
        if session is None:
            return None

        info = await session.try_get_media_properties_async()
        timeline = session.get_timeline_properties()
        playback_info = session.get_playback_info()

        if not info or not info.title:
            return None

        position = timeline.position.total_seconds() if timeline else 0.0
        end_time = timeline.end_time.total_seconds() if timeline else 0.0
        start_time = timeline.start_time.total_seconds() if timeline else 0.0
        duration = max(end_time - start_time, 0.0)

        is_playing = False
        if playback_info and playback_info.playback_status is not None:
            is_playing = playback_info.playback_status == PlaybackStatus.PLAYING

        return NowPlaying(
            title=info.title or "",
            artist=info.artist or "",
            album=info.album_title or "",
            position=position,
            duration=duration,
            is_playing=is_playing,
            app=session.source_app_user_model_id or "",
        )
