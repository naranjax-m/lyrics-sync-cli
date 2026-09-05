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
    python main.py --ascii
    python main.py --search "artist track name"
    python main.py --search "artist track name" --install ~/Lyrics
    python main.py --search "artist track name" --txtinstall ~/Lyrics
    python main.py --search "artist track name" --dminstall ~/Lyrics
"""

import argparse
import os
import re
import time
import sys

from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from now_playing import get_backend, NowPlaying
from lyrics_provider import (
    fetch_lyrics,
    current_line_index,
    search_songs,
    parse_lrc,
    LyricsResult,
)
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
    parser.add_argument(
        "--search", metavar="QUERY", default=None,
        help="Search LRCLIB for a song by title/artist (e.g. "
             "--search \"Artist Name - Song Title\") and display its "
             "lyrics, without needing anything to be currently playing.",
    )
    parser.add_argument(
        "--install", metavar="DIR", default=None,
        help="Used together with --search. Saves the selected song's "
             "lyrics into DIR: as a .lrc file (with timestamps) if "
             "synced lyrics are available, otherwise as a .txt file.",
    )
    parser.add_argument(
        "--txtinstall", metavar="DIR", default=None,
        help="Used together with --search. Saves the selected song's "
             "lyrics into DIR as a plain .txt file (timestamps "
             "stripped), regardless of whether synced lyrics exist.",
    )
    parser.add_argument(
        "--dminstall", metavar="DIR", default=None,
        help="Used together with --search. Saves the selected song's "
             "lyrics into DIR as a .dm file (plain text content, "
             "timestamps stripped, with a .dm extension).",
    )
    return parser.parse_args()


def tracks_match(a: NowPlaying, b: NowPlaying) -> bool:
    return a.title == b.title and a.artist == b.artist


def _fmt_duration(seconds) -> str:
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        seconds = 0
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def _sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    return name or "lyrics"


def _save_file(directory: str, filename: str, content: str) -> str:
    directory = os.path.expanduser(directory)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def run_search(
    query: str,
    install_dir: str = None,
    txtinstall_dir: str = None,
    dminstall_dir: str = None,
) -> None:
    """
    Looks up `query` on LRCLIB, shows a numbered results table, lets
    the user pick one, and either displays that track's lyrics in the
    terminal or saves them to disk, depending on which --*install
    flag (if any) was passed.
    """
    console.print(f"[bold cyan]Searching LRCLIB for:[/bold cyan] {query}")
    results = search_songs(query, limit=10)

    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return

    table = Table(title=f"Results for: {query}")
    table.add_column("#", justify="right")
    table.add_column("Track")
    table.add_column("Artist")
    table.add_column("Album")
    table.add_column("Duration", justify="right")
    table.add_column("Synced?")

    for i, item in enumerate(results, start=1):
        table.add_row(
            str(i),
            item.get("trackName") or "?",
            item.get("artistName") or "?",
            item.get("albumName") or "-",
            _fmt_duration(item.get("duration")),
            "Yes" if item.get("syncedLyrics") else "No",
        )

    console.print(table)

    try:
        choice = console.input(
            "\nEnter the number of the song to view its lyrics "
            "(Enter to cancel): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice:
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(results):
            raise ValueError
    except ValueError:
        console.print("[bold red]Invalid selection.[/bold red]")
        return

    item = results[idx]
    synced_raw = item.get("syncedLyrics")
    plain_raw = item.get("plainLyrics")
    title = item.get("trackName") or "lyrics"
    artist = item.get("artistName") or ""
    header = f"{title} — {artist}" if artist else title
    base_name = _sanitize_filename(f"{title} - {artist}" if artist else title)

    if synced_raw:
        lines = parse_lrc(synced_raw)
        plain_body = "\n".join(line.text for line in lines) or "(empty)"
    elif plain_raw:
        plain_body = plain_raw
    else:
        plain_body = "No lyrics available for this track on LRCLIB."

    saved_paths = []

    if install_dir:
        if synced_raw:
            path = _save_file(install_dir, f"{base_name}.lrc", synced_raw)
        else:
            path = _save_file(install_dir, f"{base_name}.txt", plain_body)
        saved_paths.append(path)

    if txtinstall_dir:
        path = _save_file(txtinstall_dir, f"{base_name}.txt", plain_body)
        saved_paths.append(path)

    if dminstall_dir:
        path = _save_file(dminstall_dir, f"{base_name}.dm", plain_body)
        saved_paths.append(path)

    if saved_paths:
        for path in saved_paths:
            console.print(f"[bold green]Saved:[/bold green] {path}")
    else:
        console.print(Panel(plain_body, title=header, border_style="magenta"))


def main():
    args = parse_args()

    if args.search:
        run_search(args.search, args.install, args.txtinstall, args.dminstall)
        return

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

