"""
ui.py
-----
Terminal rendering using `rich`: displays the current lyric line
highlighted, with a small window of surrounding lines for context.

When ASCII mode is enabled (--ascii flag), instead of the context
view it renders only the current word of the current line as a big
ASCII-art banner (via pyfiglet), and that word updates as playback
moves through the line — nothing else is shown in the body.
"""

from typing import List, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

try:
    from pyfiglet import Figlet
    _PYFIGLET_AVAILABLE = True
except ImportError:
    _PYFIGLET_AVAILABLE = False

from lyrics_provider import LyricLine
from now_playing import NowPlaying

console = Console()

CONTEXT_BEFORE = 3
CONTEXT_AFTER = 4

# Font used for the ASCII-art word banner shown with --ascii
ASCII_FONT = "standard"

# Fallback duration (seconds) assumed for the last line of a song,
# since there is no "next line" timestamp to measure against.
_FALLBACK_LINE_SECONDS = 2.5


def _ascii_banner(word: str) -> Text:
    """Renders a single word as an ASCII-art banner using pyfiglet."""
    if not word:
        return Text("")
    if not _PYFIGLET_AVAILABLE:
        return Text(word, style="bold cyan")
    try:
        figlet = Figlet(font=ASCII_FONT, width=200)
        rendered = figlet.renderText(word).rstrip("\n")
    except Exception:
        return Text(word, style="bold cyan")
    return Text(rendered, style="bold cyan")


def _current_word(lines: List[LyricLine], line_index: int, position: float) -> str:
    """
    Picks which word of the current line should be shown right now,
    based on how far playback has progressed between this line's
    timestamp and the next line's timestamp.
    """
    if line_index < 0 or line_index >= len(lines):
        return ""

    line = lines[line_index]
    words = line.text.split()
    if not words:
        return ""

    start = line.timestamp
    if line_index + 1 < len(lines):
        end = lines[line_index + 1].timestamp
    else:
        end = start + _FALLBACK_LINE_SECONDS

    duration = max(end - start, 0.01)
    elapsed = max(position - start, 0.0)
    fraction = min(elapsed / duration, 0.999)

    word_index = min(int(fraction * len(words)), len(words) - 1)
    return words[word_index]


def render_frame(
    now: Optional[NowPlaying],
    lines: List[LyricLine],
    current_index: int,
    synced: bool,
    status_msg: str = "",
    ascii_mode: bool = False,
) -> Panel:
    if now:
        header = Text(f"{now.title} — {now.artist}", style="bold cyan")
        sub = Text(f"{_fmt_time(now.position)} / {_fmt_time(now.duration)}", style="dim")
    else:
        header = Text("No playback detected", style="bold red")
        sub = Text("")

    if ascii_mode and synced and lines:
        word = _current_word(lines, current_index, now.position if now else 0.0)
        body = [_ascii_banner(word)] if word else [Text("...", style="italic yellow")]
    elif not lines:
        msg = status_msg or "Looking up synced lyrics..."
        body = [Text(msg, style="italic yellow")]
    else:
        body = _context_lines(lines, current_index)

    group = Group(header, sub, Text(""), *body)
    title = "🎵 Lyrics Sync" + ("" if synced else " (no time sync available)")
    return Panel(group, title=title, border_style="magenta")


def _context_lines(lines: List[LyricLine], current_index: int) -> List[Text]:
    body_lines = []
    start = max(0, current_index - CONTEXT_BEFORE)
    end = min(len(lines), current_index + CONTEXT_AFTER + 1)
    for i in range(start, end):
        text = lines[i].text or "♪"
        if i == current_index:
            body_lines.append(Text(f"▶ {text}", style="bold white on dark_green"))
        elif i < current_index:
            body_lines.append(Text(f"  {text}", style="dim"))
        else:
            body_lines.append(Text(f"  {text}", style="grey70"))
    return body_lines


def _fmt_time(seconds: float) -> str:
    seconds = int(max(seconds, 0))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"
