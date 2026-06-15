"""One-off: convert space-aligned <pre> song pages to song.pro (ChordPro). Stdlib only."""
import glob
import os
import re
import html as _html

_TITLE = re.compile(r'<title>(.*?)</title>', re.S | re.I)
_ARTIST = re.compile(r'<p><b><pre class="yellow"[^>]*>(.*?)</pre>', re.S)
_INNER_CHORD = re.compile(r'<pre class="yellow"[^>]*>(.*?)</pre>', re.S)


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
        ins = "[" + chord + "]"
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
    body = _INNER_CHORD.sub(lambda mm: "\x00" + _html.unescape(mm.group(1)), body)
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
            chords = re.findall(r'\S+', chord_line)
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
