#!/usr/bin/env python3
"""
Lyrics Sync CLI
===============
Shows, right in your terminal, the synced lyrics of whatever is
currently playing on Spotify, YouTube, YouTube Music, or Apple Music
(web or desktop apps), automatically detected via the operating
system's own "Now Playing" APIs.

No token, API key, or login for any service is required: it uses the
information each player already publishes to the OS, and looks up the
synced lyrics on LRCLIB (https://lrclib.net), a free, public database.

Usage:
    python main.py
    python main.py --interval 0.5
"""

import argparse
import time
import sys

from rich.live import Live

from now_playing import get_backend, NowPlaying
from lyrics_provider import fetch_lyrics, current_line_index, LyricsResult
from ui import render_frame, console


def parse_args():
    parser = argparse.ArgumentParser(description="Synced lyrics in your terminal.")
    parser.add_argument(
        "--interval", type=float, default=0.5,
        help="Seconds between each update (default: 0.5)",
    )
    parser.add_argument(
        "--refresh-fps", type=float, default=4.0,
        help="UI refresh rate in FPS (default: 4.0)",
    )
    parser.add_argument(
        "--ascii", action="store_true", dest="ascii_mode",
        help="Show the current lyric word as a big ASCII-art banner, "
             "one word at a time, instead of the line-by-line view.",
    )
    return parser.parse_args()


def tracks_match(a: NowPlaying, b: NowPlaying) -> bool:
    return a.title == b.title and a.artist == b.artist


def main():
    args = parse_args()

    try:
        backend = get_backend()
    except RuntimeError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

    if not backend.is_available():
        console.print(
            "[bold red]Required system tool not found.[/bold red]\n"
            "Check README.md to install the requirement for your platform "
            "(playerctl / winsdk / nowplaying-cli)."
        )
        sys.exit(1)

    current_track: NowPlaying | None = None
    lyrics_result: LyricsResult | None = None
    status_msg = ""

    with Live(console=console, refresh_per_second=args.refresh_fps, screen=False) as live:
        while True:
            now = backend.get_current()

            if now is None:
                current_track = None
                lyrics_result = None
                live.update(render_frame(None, [], -1, synced=False, ascii_mode=args.ascii_mode))
                time.sleep(args.interval)
                continue

            if current_track is None or not tracks_match(current_track, now):
                current_track = now
                status_msg = "Looking up synced lyrics..."
                live.update(render_frame(now, [], -1, synced=False, status_msg=status_msg, ascii_mode=args.ascii_mode))
                lyrics_result = fetch_lyrics(
                    track_name=now.title,
                    artist_name=now.artist,
                    album_name=now.album,
                    duration=now.duration or None,
                )
                if lyrics_result is None:
                    status_msg = "No lyrics found for this track."
                elif not lyrics_result.synced:
                    status_msg = "Only unsynced (plain) lyrics are available."
            else:
                current_track = now

            if lyrics_result and lyrics_result.synced:
                idx = current_line_index(lyrics_result.lines, now.position)
                live.update(render_frame(now, lyrics_result.lines, idx, synced=True, ascii_mode=args.ascii_mode))
            else:
                live.update(render_frame(now, [], -1, synced=False, status_msg=status_msg, ascii_mode=args.ascii_mode))

            time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting...[/bold]")
