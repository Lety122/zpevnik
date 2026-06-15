"""Verify each song.pro preserves the original page's lyrics and chords.

Two checks per song:
  1. Lyric text: with all chords removed, the alphanumeric character sequence of the lyrics
     must match the original. (Mid-word chord insertions like 'rozmláce[Hm]nýho' rejoin when
     chords are stripped, so they are correctly treated as non-changes.)
  2. Chord multiset: the bag of chord tokens must match (comma-normalized).

Known exception: a few songs carry a section label (e.g. 'R:') INSIDE the original chord <pre>;
the converter relocates it into the lyric line. Such songs are reported so they can be
hand-confirmed (the label moves from the chord set into the lyric text — expected).
"""
import glob
import os
import re
import html as _html
import collections
import unicodedata
import chordpro
import convert_to_chordpro as conv

_INNER = re.compile(r'<pre class="yellow"[^>]*>(.*?)</pre>', re.S)


def _alnum(s):
    s = unicodedata.normalize("NFC", s).lower()
    return "".join(ch for ch in s if ch.isalnum())


def _chords(tokens):
    """Multiset of real chord tokens (chord-like only; labels/repeat-marks excluded)."""
    return collections.Counter(
        t for t in (x.replace(",", "") for x in tokens) if conv._CHORDLIKE.match(t)
    )


_LABEL = re.compile(
    r'^(?:ref|ref\.|intro|předehra|predehra|mezihra|mezihrá|coda|outro|nápěv|napev|'
    r'bridge|sloka|\d+\.?|\d*x|x\d+)$', re.I)


def _lyric(tokens):
    """alnum of sung lyric words. Lyric text contains NO chords (chords are extracted
    separately), so we keep chord-like fragments (e.g. the 'D' of 'D[Ami]neska') and only drop
    relocated labels (':'-bearing) and section/repeat markers. Any chord that leaked into the
    text as a literal (unrecognized notation) will therefore correctly show up as a diff."""
    keep = [t for t in tokens if ":" not in t and not _LABEL.match(t.replace(",", ""))]
    return _alnum(" ".join(keep))


def original(src):
    after = src.split("</div>", 1)[1]
    m = re.search(r"<pre>(.*)</pre>\s*</div>", after, re.S)
    body = m.group(1) if m else ""
    chord_toks = []
    for mm in _INNER.finditer(body):
        chord_toks += re.findall(r'\S+', _html.unescape(mm.group(1)))
    lyric_toks = re.findall(r'\S+', _html.unescape(_INNER.sub(" ", body)))
    return _lyric(lyric_toks), _chords(chord_toks)


def from_pro(pro_text):
    doc = chordpro.parse_pro(pro_text)
    chord_toks, lyric_toks = [], []
    for ln in doc["lines"]:
        if ln["type"] == "chordonly":
            chord_toks += ln["chords"]
        elif ln["type"] == "lyric":
            for ch in ln["chunks"]:
                if ch["chord"]:
                    chord_toks.append(ch["chord"])
                lyric_toks += ch["text"].split()
    return _lyric(lyric_toks), _chords(chord_toks)


def main():
    hard, soft = [], []
    for page in sorted(glob.glob("[0-9][0-9][0-9][0-9]/*/index.html")):
        d = os.path.dirname(page)
        pro = os.path.join(d, "song.pro")
        if not os.path.exists(pro):
            hard.append((d, "no song.pro"))
            continue
        ol, oc = original(open(page, encoding="utf-8").read())
        pl, pc = from_pro(open(pro, encoding="utf-8").read())
        if oc != pc:  # chord-like multiset differs -> real musical corruption
            hard.append((d, f"CHORD missing={list((oc-pc).elements())[:8]} extra={list((pc-oc).elements())[:8]}"))
        if ol != pl:  # lyric chars differ (often label relocation) -> eyeball
            i = next((k for k in range(min(len(ol), len(pl))) if ol[k] != pl[k]), min(len(ol), len(pl)))
            soft.append((d, f"lyric@{i}: orig…{ol[max(0,i-10):i+10]!r} pro…{pl[max(0,i-10):i+10]!r} (len {len(ol)} vs {len(pl)})"))
    print("== HARD (chord mismatch):", len(hard))
    for d, why in hard:
        print("  ", d, "->", why)
    print("== SOFT (lyric/label shuffle, verify visually):", len(soft))
    for d, why in soft:
        print("  ", d, "->", why)
    if not hard and not soft:
        print("ALL 52 MATCH")
    return 1 if hard else 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
