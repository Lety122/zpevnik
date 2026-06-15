"""One-off: convert space-aligned <pre> song pages to song.pro (ChordPro). Stdlib only."""
import glob
import os
import re
import html as _html

_TITLE = re.compile(r'<title>(.*?)</title>', re.S | re.I)
_ARTIST = re.compile(r'<p><b><pre class="yellow"[^>]*>(.*?)</pre>', re.S)
_INNER_CHORD = re.compile(r'<pre class="yellow"[^>]*>(.*?)</pre>(\n?)', re.S)


def extract_title(src):
    m = _TITLE.search(src)
    return _html.unescape(m.group(1).strip()) if m else ""


def extract_artist(src):
    m = _ARTIST.search(src)
    return _html.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip()) if m else ""


def merge(chord_line, lyric_line):
    """Insert [chord] tokens into lyric at the chord's column. Returns a ChordPro line."""
    tokens = [(m.start(), m.group(0)) for m in re.finditer(r'\S+', chord_line)]
    result = list(lyric_line)
    for col, chord in sorted(tokens, reverse=True):  # rightmost first keeps indices valid
        ins = "[" + chord.strip(",") + "]"
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
        if not lines:
            return mm.group(2)
        if mm.group(2) == "\n":
            # Standalone chord block (</pre> on its own line): every non-blank line is a chord line.
            return "\n".join(("\x00" + ln if ln.strip() else ln) for ln in lines) + "\n"
        # </pre> followed by same-line lyric text: the last inner line is a lyric-prefix label
        # (e.g. "R:"); earlier lines are chord lines that merge with label+following text.
        chord_lines = lines[:-1]
        marked = "\n".join("\x00" + ln for ln in chord_lines if ln.strip())
        return (marked + "\n" if marked else "") + lines[-1]

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
            out.append(" ".join("[" + c + "]" for c in chords))
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
    return f"{{title: {title}}}\n{{artist: {artist}}}\n\n" + "\n".join(pro) + "\n"


def main():
    for page in sorted(glob.glob("[0-9][0-9][0-9][0-9]/*/index.html")):
        pro = convert(open(page, encoding="utf-8").read())
        out = os.path.join(os.path.dirname(page), "song.pro")
        open(out, "w", encoding="utf-8").write(pro)
        print("wrote", out)


if __name__ == "__main__":
    main()
