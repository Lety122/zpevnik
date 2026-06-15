"""One-off: convert space-aligned <pre> song pages to song.pro (ChordPro). Stdlib only."""
import glob
import os
import re
import html as _html

_TITLE = re.compile(r'<title>(.*?)</title>', re.S | re.I)
_ARTIST = re.compile(r'<p><b><pre class="yellow"[^>]*>(.*?)</pre>', re.S)
_INNER_CHORD = re.compile(r'<pre class="yellow"[^>]*>(.*?)</pre>([^\S\n]*)(\n?)', re.S)
# Root (A-H + optional accidental) followed only by chord-quality characters. Excludes word
# labels like "Coda"/"Bridge" (their letters aren't valid quality chars) but accepts extended
# chords like G7+5, Am7b5, C#sus4, D/F#.
_CHORDLIKE = re.compile(
    r'^[A-H][#b]?(?:maj|min|mi|m|dim|aug|sus|add|°|[0-9+\-#b*()])*(?:/[A-H][#b]?)?$')


def _is_chord_line(s):
    """True if every token looks like a chord or a structural marker (|: :| 2x ...)."""
    toks = s.split()
    if not toks:
        return False
    for t in toks:
        if _CHORDLIKE.match(t):
            continue
        if re.match(r'^\(?\d+x\)?$', t):  # repeat counts like 2x, (3x)
            continue
        if set(t) <= set("|:[]()"):       # bar/repeat punctuation
            continue
        return False
    return True


def extract_title(src):
    m = _TITLE.search(src)
    return _html.unescape(m.group(1).strip()) if m else ""


def extract_artist(src):
    m = _ARTIST.search(src)
    return _html.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip()) if m else ""


_REPEAT = {"[:": "|:", ":]": ":|"}  # bracket repeats break [chord] parsing -> use pipe form


def _emit(tok):
    """Chord-like token -> '[chord]'; repeat marker -> pipe form; anything else -> literal.

    Labels stuffed into chord lines (e.g. 'Ref.:', 'R:', '1.') must NOT be bracketed, or they
    become bogus chords and corrupt parsing.
    """
    t = tok.strip(",")
    if t in _REPEAT:
        return _REPEAT[t]
    if _CHORDLIKE.match(t):
        return "[" + t + "]"
    if t.startswith("(") and t.endswith(")") and _CHORDLIKE.match(t[1:-1]):
        return "[" + t + "]"  # parenthesized passing chord, e.g. (Ami)
    return t


def merge(chord_line, lyric_line):
    """Insert [chord] tokens into lyric at the chord's column. Returns a ChordPro line."""
    tokens = [(m.start(), m.group(0)) for m in re.finditer(r'\S+', chord_line)]
    result = list(lyric_line)
    for col, chord in sorted(tokens, reverse=True):  # rightmost first keeps indices valid
        ins = _emit(chord)
        if col >= len(result):
            result = result + list(" " * (col - len(result)))
            result.append(ins)
        else:
            result.insert(col, ins)
    return "".join(result).rstrip()


def _song_body(src):
    """Inner text of the main song <pre>, with chord <pre> lines marked by a leading \\x00."""
    after = src.split("</div>", 1)[1] if "</div>" in src else src
    m = re.search(r"<pre>(.*)</pre>\s*</div>", after, re.S)
    body = m.group(1) if m else ""

    def _mark(mm):
        # An inner chord <pre> may hold several chord lines; mark EACH non-blank one with \x00.
        # Strip blank lines from the block's edges (tag-formatting newlines), keep internal ones.
        lines = _html.unescape(mm.group(1)).split("\n")
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()
        spaces, nl = mm.group(2), mm.group(3)
        if not lines:
            return spaces + nl

        def mark_all():
            return "\n".join(("\x00" + ln if ln.strip() else ln) for ln in lines)

        if nl == "\n":
            # Standalone chord block (</pre> then only spaces then newline): all chord lines.
            return mark_all() + "\n"
        # Text follows on the same line after </pre> (that text is lyric).
        if _is_chord_line(lines[-1]):
            # Last inner line is a real chord line -> all lines are chords; force a newline so
            # the following same-line lyric becomes its own line and pairs with the last chord.
            return mark_all() + "\n"
        # Last inner line is a label (e.g. "R:"): it prefixes the following lyric text.
        chord_lines = lines[:-1]
        marked = "\n".join("\x00" + ln for ln in chord_lines if ln.strip())
        return (marked + "\n" if marked else "") + lines[-1] + spaces

    body = _INNER_CHORD.sub(_mark, body)
    return _html.unescape(body)


def convert(src):
    title = extract_title(src)
    artist = extract_artist(src)
    raw_lines = _song_body(src).split("\n")
    out = []
    i = 0
    while i < len(raw_lines):
        ln = raw_lines[i]
        if ln.startswith("\x00"):
            chord_line = ln[1:]
            nxt = raw_lines[i + 1] if i + 1 < len(raw_lines) else ""
            if nxt and not nxt.startswith("\x00") and nxt.strip() != "":
                out.append(merge(chord_line, nxt))
                i += 2
                continue
            chords = re.findall(r'[^\s,]+', chord_line)
            out.append(" ".join(_emit(c) for c in chords))
            i += 1
            continue
        out.append(ln.rstrip())
        i += 1
    pro = []
    for ln in out:
        if ln.strip() == "" and (not pro or pro[-1] == ""):
            continue  # collapse consecutive blanks
        pro.append(ln)
    while pro and pro[-1] == "":
        pro.pop()
    body_text = "\n".join(pro)
    # Catch any stray bracket-repeat markers left in lyric text (e.g. "R: [:" labels) so they
    # don't break [chord] parsing downstream.
    body_text = body_text.replace("[:", "|:").replace(":]", ":|")
    return f"{{title: {title}}}\n{{artist: {artist}}}\n\n" + body_text + "\n"


def main():
    for page in sorted(glob.glob("[0-9][0-9][0-9][0-9]/*/index.html")):
        pro = convert(open(page, encoding="utf-8").read())
        out = os.path.join(os.path.dirname(page), "song.pro")
        open(out, "w", encoding="utf-8").write(pro)
        print("wrote", out)


if __name__ == "__main__":
    main()
