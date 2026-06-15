# ChordPro format + renderer, transpose, font-size control

Date: 2026-06-15
Status: approved

## Goal

Replace the hand-aligned `<pre>` chord/lyric format with a ChordPro source format and a
generator that renders it to static HTML. This:

- Fixes mobile horizontal overflow at the root (inline chords reflow with lyrics instead of
  wide monospace lines), retiring the shrink-to-fit script.
- Enables chord transpose (chords become data, not baked-in spaces).
- Makes authoring songs far easier (type lyrics, drop `[chord]` inline).

Keeps the project's core strengths: zero runtime dependencies, static output, rsync deploy,
offline PWA.

## Decisions (locked)

- Auto-convert all 52 existing songs now; source of truth becomes `song.pro` per dir.
- Include transpose (±semitone) now.
- Include user font-size control now.

## Architecture

### Source of truth & build flow

- Each song dir gets `song.pro` (ChordPro text) — the editable source.
- `py-gen.py` renders `index.html` per song from its `song.pro`, AND regenerates the search
  list in the root `index.html` + `urlsToCache` in `sw.js` + bumps `CACHE_NAME` (as today).
- `předloha.html` is replaced by `predloha.pro` (ChordPro template). The HTML template lives
  in the `py-gen.py` renderer.
- `*.pro` files are source only — excluded from the rsync in `deploy.sh`.
- Adding/editing a song = edit `song.pro` → `./deploy.sh`.

### ChordPro format (subset we support)

```
{title: Anděl}
{artist: Karel Kryl}

[D, A7]
[D]Z rozmlácenýho [Hm]kostela v krabici s [D]kusem [A7]mýdla,
R: [D]A proto prosím [Hm]věř mi, chtěl jsem ho žádat,
```

- `{title: ...}` and `{artist: ...}` directives (one each, at top).
- Inline `[chord]` placed immediately before the syllable it sits above.
- Chord-only line: a line whose non-whitespace content is only `[chord]` tokens (intro /
  instrumental / outro). Rendered as a row of chords with no lyric beneath.
- Any other text (section labels like `R:`, `Nápěv:`, repeat markers `|: :|`) is preserved
  verbatim as lyric text; chords may be embedded in it.
- Blank lines preserved as stanza separation.

### Converter — one-off migration script `convert_to_chordpro.py`

Input: existing `*/*/index.html`. Output: `song.pro` next to each.

Algorithm per song body (the outer `<pre>`):
1. Tokenize the outer `<pre>` into an ordered sequence of: inner `<pre class="yellow">CHORDS</pre>`
   chord lines, plain lyric text lines, and blank lines.
2. Pair each chord line with the lyric line that immediately follows it.
   - For each chord token at column `c` in the chord line, insert `[chord]` into the lyric
     before the character currently at column `c` (track insertion offset). Chords past the
     lyric's end are appended at the end of the line.
   - A chord line with no following lyric line (next item is another chord line, blank, or
     end) becomes a chord-only line: `[D] [A7] ...`.
3. Lyric lines with no chord line above them pass through as plain text.
4. Title from `<title>`; artist from the author `<pre>` (`font-size: 20px`). Emit as directives.

### Renderer — `render_song(pro_text) -> html` in `py-gen.py`

- Parse directives + lines.
- Lyric line: split into chunks at `[chord]` boundaries. Each `[chord]text` →
  `<span class="ch"><span class="c" data-chord="D">D</span>text</span>`. Leading text before
  the first chord is a chunk with an empty chord slot.
- Chord-only line → row of `<span class="c" data-chord="...">` (a `.chordrow`).
- Plain text line (no chords) → rendered as text, may hold section labels.
- Emit full page from a single HTML template string: head/styles, title, artist, controls
  (transpose ±, font-size ±/reset, back-to-list), song body, then the wake-lock + SW-register
  scripts (reused as today).

### CSS (chord above lyric, reflowing)

```
.ch { display: inline-block; vertical-align: bottom; white-space: nowrap; }
.ch .c { display: block; color: #FEB12C; font-weight: bold; font-size: .8em;
         line-height: 1; height: 1.1em; }
.chordrow .c { display: inline-block; margin-right: 1ch; }
```

Words wrap between chunks; each chord stays glued above its word. Lyrics reflow to viewport
width → no horizontal overflow. The previous fit-to-width shrink script is removed; keep only
`body { overflow-x: hidden }` as a safety.

### Transpose

- Each chord span carries `data-chord` (original, untransposed).
- Client JS: semitone offset, +/- buttons. Re-derives each chord's displayed text from
  `data-chord` + offset. Persisted per song in `localStorage` (key by pathname).
- Czech notation aware: input uses `H` = B natural and `B` = B-flat. Internal 12-tone scale
  maps `H`→11, `B`→10 (and `A#`→`B`, etc. on output we prefer Czech `H`/`B` spelling).
  Parser handles root, accidental (`#`/`b`), and slash bass (`D/F#`), preserving the suffix
  (`m`, `7`, `maj7`, `sus4`, `mi`, `dim`, ...).

### Font-size control

- +/- and reset buttons. Offset persisted globally in `localStorage`.
- Applied to the song body container font-size (chords scale via `em`).

## Verification (risk gate)

The conversion must not corrupt songs. After convert → render, for EVERY song:

1. Content-equality check: extract the ordered (chord, following-text) token sequence from the
   ORIGINAL page and from the NEW rendered page; assert they match (ignoring whitespace-only
   differences). Any mismatch → flagged, fixed by hand before shipping.
2. Visual spot-check: screenshot-diff a representative sample (incl. a long song, a long-title
   song, a chord-only-intro song, an English song) old vs new at mobile width.

Nothing ships unverified. List any songs that needed manual fixes.

## Out of scope

- Lyrics search, author-in-list (separate future wins).
- Full ChordPro spec (`{soc}`, `{define}`, tabs) — only the subset above.

## Rollback

`song.pro` + generated `index.html` are committed; the pre-migration HTML is in git history.
If a render regresses, revert the commit.
