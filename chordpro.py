"""ChordPro parsing + HTML rendering for the songbook. Stdlib only."""
import re
import html as _html

_DIRECTIVE = re.compile(r'^\{(\w+):\s*(.*?)\s*\}$')
_CHORD = re.compile(r'\[([^\]]*)\]')


def parse_pro(text):
    """ChordPro text -> {'title','artist','lines':[...]}.

    Line types:
      {'type':'blank'}
      {'type':'chordonly','chords':[...]}
      {'type':'lyric','chunks':[{'chord','text'},...]}
    """
    title = artist = ""
    lines = []
    raw_lines = text.split("\n")
    if raw_lines and raw_lines[-1] == "":
        raw_lines.pop()  # drop the final-newline terminator artifact
    for raw in raw_lines:
        line = raw.rstrip("\r")
        m = _DIRECTIVE.match(line.strip())
        if m:
            key, val = m.group(1).lower(), m.group(2)
            if key == "title":
                title = val
            elif key == "artist":
                artist = val
            continue
        if line.strip() == "":
            lines.append({"type": "blank"})
            continue
        # chord-only line: removing all [..] tokens leaves only whitespace/punctuation
        stripped = _CHORD.sub("", line)
        if stripped.strip(" ,|:") == "" and _CHORD.search(line):
            flat = []
            for c in _CHORD.findall(line):
                flat.extend(p.strip() for p in c.split(",") if p.strip())
            lines.append({"type": "chordonly", "chords": flat})
            continue
        lines.append({"type": "lyric", "chunks": _split_chunks(line)})
    return {"title": title, "artist": artist, "lines": lines}


def _split_chunks(line):
    chunks = []
    pos = 0
    leading = True
    for m in _CHORD.finditer(line):
        text_before = line[pos:m.start()]
        if leading:
            if text_before != "":
                chunks.append({"chord": "", "text": text_before})
            leading = False
        else:
            chunks[-1]["text"] = text_before
        chunks.append({"chord": m.group(1), "text": ""})
        pos = m.end()
    if not chunks:
        return [{"chord": "", "text": line}]
    chunks[-1]["text"] = line[pos:]
    return chunks


def _esc(s):
    return _html.escape(s, quote=True)


def render_song_body(lines):
    """List of parsed lines -> HTML string for the song body."""
    out = []
    for ln in lines:
        if ln["type"] == "blank":
            out.append("")
            continue
        if ln["type"] == "chordonly":
            spans = "".join(
                f'<span class="c" data-chord="{_esc(c)}">{_esc(c)}</span>' for c in ln["chords"]
            )
            out.append(f'<div class="chordrow">{spans}</div>')
            continue
        spans = []
        for ch in ln["chunks"]:
            spans.append(
                f'<span class="ch"><span class="c" data-chord="{_esc(ch["chord"])}">'
                f'{_esc(ch["chord"])}</span>{_esc(ch["text"])}</span>'
            )
        out.append(f'<div class="line">{"".join(spans)}</div>')
    return "\n".join(out)
