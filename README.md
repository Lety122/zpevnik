# Ultimátní Zpěvník

A static, offline-capable songbook (PWA) of song lyrics with chords. Live at
**https://zpevnik.droplet.cz**.

Each song is written once in [ChordPro](#song-format) format (`song.pro`) and a small Python
build step renders it to a standalone HTML page. No frameworks, no runtime dependencies — the
deployed site is plain static files served over rsync.

## Features

- **Search** — instant, diacritics-insensitive title search (typing `tri krize` finds *Tři kříže*).
- **Transpose** — shift chords ±1 semitone, persisted per song. Czech notation aware
  (`H` = B natural, `B` = B-flat, slash chords like `D/F#`).
- **Font size** — per-device A−/A+ control, persisted globally.
- **Wake lock** — screen stays on while a song is open.
- **Offline PWA** — installable on Android/iOS/desktop; service worker caches all songs.

## How it works

```
YYYY/<slug>/song.pro   ← source of truth (you edit this)
        │
        │  python3 py-gen.py
        ▼
YYYY/<slug>/index.html  ← rendered song page  (generated)
index.html              ← search list updated  (generated block)
sw.js                   ← offline cache list + bumped version (generated block)
        │
        │  ./deploy.sh  (runs py-gen.py, then rsync)
        ▼
   VPS web root → https://zpevnik.droplet.cz
```

| File | Role |
|------|------|
| `chordpro.py` | ChordPro parser + HTML renderer (page template lives here). Stdlib only. |
| `py-gen.py` | Build script: renders every `song.pro`, rebuilds search list in `index.html`, rebuilds `urlsToCache` in `sw.js` and bumps `CACHE_NAME`. |
| `deploy.sh` | Runs the build, then rsyncs only the static site to the VPS. |
| `index.html` | Root page: search box + song list (the list is a generated block). |
| `sw.js` | Service worker: offline cache (the URL list + cache version are generated). |
| `manifest.json` | PWA manifest. |
| `predloha.pro` | Template / cheat-sheet for a new song. |
| `tests/` | pytest tests for the parser/renderer. |
| `convert_to_chordpro.py`, `verify_conversion.py` | One-off migration tools (legacy HTML → ChordPro). Not used in normal workflow. |

`*.pro` source files, the Python scripts, `tests/`, and `docs/` are **excluded** from the
deployed site — only the static output ships.

## Song format

A song lives in `YEAR/<slug>/song.pro`. The year folder is just organization; `slug` is the URL
segment (lowercase, hyphenated, ASCII). Minimal example:

```
{title: Anděl}
{artist: Karel Kryl}

[D] [A7]
[D]Z rozmláce[Hm]nýho kostela [D]v krabici [A7]s kusem mýdla,
R: [D]A proto [Hm]prosím věř mi, [D]chtěl jsem ho [A7]žádat,

Prázdný řádek = mezera mezi slokami.
```

Rules:

- `{title: ...}` and `{artist: ...}` at the top. **Title is required** (a song without one is
  skipped from the build with a warning).
- Put `[chord]` inline, immediately before the syllable it sits above. Chords render above the
  lyric and reflow with the text — no horizontal overflow on mobile.
- **Chord-only line** (intro / instrumental / outro): a line containing only `[chord]` tokens,
  e.g. `[Hm] [G] [A] [D]`. Renders as a standalone row of chords.
- Section labels (`R:`, `Nápěv:`, …) and repeat markers (`|: :|`) are plain text — write them at
  the start of the line; chords can still be embedded.
- A blank line = stanza break.

`predloha.pro` is a ready-to-copy template.

## Add or edit a song

1. Create the folder and source file:
   ```bash
   mkdir -p 2026/nova-pisnicka
   cp predloha.pro 2026/nova-pisnicka/song.pro
   ```
2. Edit `2026/nova-pisnicka/song.pro` — set `{title}` / `{artist}`, write lyrics with inline
   `[chord]`s.
3. Build locally to render and preview:
   ```bash
   python3 py-gen.py
   ```
   This rewrites the song's `index.html`, adds it to the search list in the root `index.html`,
   adds it to the offline cache in `sw.js`, and bumps the cache version. Open the root
   `index.html` (or the song's `index.html`) in a browser to check.
4. Deploy (see below). `deploy.sh` runs the build again, so step 3 is only for local preview.

To **edit** an existing song, just change its `song.pro` and rebuild/deploy — same flow.

> Note: editing generated files (`index.html`, `sw.js`) by hand is pointless — the build
> overwrites the generated blocks. Edit `song.pro` instead.

## Run locally

It's static HTML; serve the folder with anything, e.g.:

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

(The service worker needs to be served over HTTP, not opened as a `file://` path.)

## Tests

```bash
python3 -m pytest tests/
```

Covers the ChordPro parser and renderer.

## Deploy

```bash
./deploy.sh
```

What it does:

1. Runs `python3 py-gen.py` (re-render songs, rebuild search list + cache list, bump cache version).
2. `rsync --delete` of the static site to `pavel-vps:/var/www/zpevnik.jelinekp.cz/`, excluding all
   source/build files (`*.pro`, Python scripts, `tests/`, `docs/`, `.git`, `__pycache__`).

Canonical URL is **https://zpevnik.droplet.cz**; `jelinekp.cz` 301-redirects to it.

Then commit the source + generated files:

```bash
git add -A && git commit
```

### Prerequisites

- SSH access to the VPS via the `pavel-vps` host alias (configure in `~/.ssh/config`).
- One-time, on the VPS: make the web root writable by your user —
  `sudo chown -R pavel:pavel /var/www/zpevnik.jelinekp.cz` (sudo needs a password).
- Bumping `CACHE_NAME` (done automatically by the build) is what forces clients to fetch the
  updated content past the service-worker cache.
