# Lyrics Sync CLI

Shows the **synced lyrics** for whatever you're currently listening to
on **Spotify, YouTube, YouTube Music, or Apple Music** (desktop apps
or browser tabs), right in your terminal — with **automatic detection
and no token, API key, or login required.**

## How does it work without tokens?

Instead of connecting to each service's private API (which would
require credentials), the program reads the **"now playing"**
information that the operating system itself already maintains for
any media player:

| OS       | Mechanism used                                                |
|----------|----------------------------------------------------------------|
| Linux    | MPRIS via D-Bus (`playerctl`)                                   |
| Windows  | `GlobalSystemMediaTransportControlsSessionManager` (GSMTC)      |
| macOS    | `MediaRemote` framework (via `nowplaying-cli`)                  |

Since Spotify, and browsers playing YouTube, YouTube Music, or Apple
Music, integrate automatically with these system-level controls, the
program detects title, artist, album, and playback position without
integrating with each service individually.

Synced lyrics are looked up in real time on
[LRCLIB](https://lrclib.net), a free, public database of lyrics in LRC
format that requires no authentication.

# Install
>Arch

The project includes `.sh` scripts that do everything automatically:

```bash
git clone https://github.com/naranjax-m/lyrics-sync-cli
cd lyrics-sync-cli
chmod +x install.sh run.sh uninstall.sh
./install.sh
chmod +x install-global.sh
./install-global.sh
```

`install.sh` does the following:
1. Installs `playerctl` via `pacman` (MPRIS/D-Bus detection mechanism), if not already installed.
2. Checks that `python`/`pip` are available (installs them if missing).
3. Creates a virtual environment (`venv/`) and installs the dependencies from `requirements.txt` inside it.
4. Adds a `lyrics-sync` shell **alias** (pointing at this project's `run.sh`) to your `~/.bashrc` and/or `~/.zshrc`, so you can just type `lyrics-sync` from that shell.

To **start the program** after installing:

```bash
lyrics-sync
```

or, once you've opened a new terminal (or run `source ~/.bashrc` / `source ~/.zshrc`):

```bash
lyrics-sync
```

`lyrics-sync` automatically activates the virtual environment and runs
`main.py`. Any argument you pass gets forwarded to the program, e.g.:

```bash
lyrics-sync --interval 0.3      # refresh playback position more often
lyrics-sync --refresh-fps 8     # refresh the UI more often
lyrics-sync --ascii             # show the current word as a big ASCII-art banner
```

The same works through the alias: `lyrics-sync --ascii`, etc.

To **remove the virtual environment** (e.g. to reinstall from scratch):

```bash
./uninstall.sh
```

> For YouTube, YouTube Music, or Apple Music (web) to show up, just
> have them playing in a Chrome, Firefox, or any Chromium/Firefox-based
> browser tab: they expose the Media Session API via MPRIS
> automatically, just like Spotify.

## Manual installation (other distros / other systems)

### 1. Install the Python dependencies

```bash
cd lyrics-sync-cli
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install the requirement for your OS

**Linux** (Debian/Ubuntu): `sudo apt install playerctl`
**Linux** (Fedora): `sudo dnf install playerctl`
**Linux** (Arch): `sudo pacman -S playerctl` (or use `./install.sh`, see above)

**Windows**: nothing extra to install at the system level; `winsdk`
(already included in `requirements.txt`) accesses Windows' native API
directly.

**macOS**: `brew install nowplaying-cli`

### 3. Run it

```bash
python main.py
```

## Look up any song with `--search`

You don't need anything to be playing to look up lyrics: `--search`
queries LRCLIB directly by title/artist, shows a numbered table of
matches, and lets you pick one to view.

```bash
./run.sh --search "Artist Name - Song Title"
```

## Save a song's lyrics directly with `--install`

If you already know which song you want and don't need the
interactive picker, use `--install` (or one of its variants) with two
arguments — the destination folder and the song to look for. The
closest match on LRCLIB is picked automatically and its lyrics are
saved into that folder; `~` is expanded automatically.

```bash
./run.sh --install       [DESTINATION FOLDER] [song name or closest match]
./run.sh --txtinstall    [DESTINATION FOLDER] [song name or closest match]
./run.sh --dminstall     [DESTINATION FOLDER] [song name or closest match]
```

| Flag             | Output                                                                 |
|------------------|-------------------------------------------------------------------------|
| `--install`      | Saves a `.lrc` file (with timestamps) if synced lyrics exist, otherwise a `.txt` file. |
| `--txtinstall`   | Always saves a plain `.txt` file (timestamps stripped).                 |
| `--dminstall`    | Same content as `--txtinstall`, saved with a `.dm` extension instead.   |

Examples:

```bash
./run.sh --install ~/Lyrics "Artist Name - Song Title"
./run.sh --txtinstall ~/Lyrics "Artist Name - Song Title"
./run.sh --dminstall ~/Lyrics "Artist Name - Song Title"
```

These flags (and `--search`) run independently of the now-playing
mode — no music needs to be playing, and the normal now-playing mode
never writes anything to disk.

## ASCII word mode (`--ascii`)

Pass `--ascii` to switch the lyric display from the line-by-line view
to a **big ASCII-art banner showing only the current word**, rendered
with [pyfiglet](https://github.com/pwaller/pyfiglet) (pure Python, no
external `figlet` binary needed). The word updates automatically as
playback advances through the line — nothing else is shown in that
area, just one word at a time.

```bash
./run.sh --ascii
```

## Notes and limitations

- If a track isn't in LRCLIB's database, or only exists as plain
  lyrics (no timestamps), the program will let you know on screen.
- The Apple Music desktop app on Windows/Linux doesn't always expose
  full metadata; it works best on macOS via `nowplaying-cli`.
- This project doesn't download, store, or redistribute lyrics — it
  fetches them live from LRCLIB to display while you listen.

## Project structure

```
lyrics-sync-cli/
├── main.py                 # Entry point / main loop
├── ui.py                   # Terminal UI (rich)
├── lyrics_provider.py       # LRCLIB client + LRC format parser
├── now_playing/
│   ├── __init__.py         # Backend selection based on OS
│   ├── linux.py            # MPRIS / playerctl backend
│   ├── windows.py          # GSMTC / winsdk backend
│   └── macos.py            # MediaRemote / nowplaying-cli backend
├── install.sh              # Automatic installation (Arch Linux)
├── run.sh                  # Activates the environment and runs the program
├── uninstall.sh            # Removes the virtual environment
├── install-global.sh       # Creates a global "lyrics-sync" command (any session)
├── requirements.txt
└── README.md
```
