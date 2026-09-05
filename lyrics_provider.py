"""
lyrics_provider.py
------------------
Fetches synced lyrics (LRC format) from LRCLIB (https://lrclib.net),
a free, public API that requires NO token or API key.

Public docs: https://lrclib.net/docs
"""

import re
import requests
from dataclasses import dataclass
from typing import List, Optional

LRCLIB_BASE = "https://lrclib.net/api"


@dataclass
class LyricLine:
    timestamp: float  # seconds
    text: str


@dataclass
class LyricsResult:
    synced: bool
    lines: List[LyricLine]
    plain_text: Optional[str] = None
    source: str = "LRCLIB"


_TIME_TAG_RE = re.compile(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]")


def parse_lrc(lrc_text: str) -> List[LyricLine]:
    """Converts a block of LRC-formatted text into a list of LyricLine."""
    lines: List[LyricLine] = []
    for raw_line in lrc_text.splitlines():
        matches = list(_TIME_TAG_RE.finditer(raw_line))
        if not matches:
            continue
        # The text is whatever remains after stripping all time tags
        text = _TIME_TAG_RE.sub("", raw_line).strip()
        for m in matches:
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            millis_str = m.group(3) or "0"
            # normalize to milliseconds (2 or 3 digits)
            millis = int(millis_str.ljust(3, "0")[:3])
            ts = minutes * 60 + seconds + millis / 1000.0
            lines.append(LyricLine(timestamp=ts, text=text))
    lines.sort(key=lambda l: l.timestamp)
    return lines


def fetch_lyrics(
    track_name: str,
    artist_name: str,
    album_name: str = "",
    duration: Optional[float] = None,
    timeout: float = 6.0,
) -> Optional[LyricsResult]:
    """
    Looks up lyrics on LRCLIB. First tries /get (exact match, ideal when
    the exact track duration is known) and falls back to /search
    (fuzzy match) if that fails.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "lyrics-sync-cli/1.0"})

    # 1) Exact match attempt
    if duration:
        try:
            params = {
                "track_name": track_name,
                "artist_name": artist_name,
                "album_name": album_name,
                "duration": int(round(duration)),
            }
            r = session.get(f"{LRCLIB_BASE}/get", params=params, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                result = _parse_api_item(data)
                if result:
                    return result
        except requests.RequestException:
            pass

    # 2) Fuzzy search
    try:
        query = f"{artist_name} {track_name}".strip()
        r = session.get(
            f"{LRCLIB_BASE}/search",
            params={"track_name": track_name, "artist_name": artist_name} if artist_name else {"q": query},
            timeout=timeout,
        )
        if r.status_code == 200:
            items = r.json()
            if isinstance(items, list) and items:
                # Prefer the first item that has synced lyrics
                best = next((it for it in items if it.get("syncedLyrics")), items[0])
                result = _parse_api_item(best)
                if result:
                    return result
    except requests.RequestException:
        pass

    return None


def _parse_api_item(data: dict) -> Optional[LyricsResult]:
    if not data:
        return None
    synced_raw = data.get("syncedLyrics")
    plain_raw = data.get("plainLyrics")
    if synced_raw:
        lines = parse_lrc(synced_raw)
        if lines:
            return LyricsResult(synced=True, lines=lines, plain_text=plain_raw)
    if plain_raw:
        return LyricsResult(synced=False, lines=[], plain_text=plain_raw)
    return None


def current_line_index(lines: List[LyricLine], position_seconds: float) -> int:
    """Returns the index of the line that matches the current playback position."""
    idx = -1
    for i, line in enumerate(lines):
        if line.timestamp <= position_seconds:
            idx = i
        else:
            break
    return idx
