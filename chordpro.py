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
            out.append('<div class="br"></div>')
            continue
        if ln["type"] == "chordonly":
            spans = "".join(
                f'<span class="c" data-chord="{_esc(c)}">{_esc(c)}</span>' for c in ln["chords"]
            )
            out.append(f'<div class="chordrow">{spans}</div>')
            continue
        # Drop cosmetic leading indentation from the source so all lines left-align.
        chunks = [dict(c) for c in ln["chunks"]]
        while chunks and chunks[0]["chord"] == "" and not chunks[0]["text"].strip():
            chunks.pop(0)
        if chunks and chunks[0]["chord"] == "":
            chunks[0]["text"] = chunks[0]["text"].lstrip()

        # Split each chunk's text at spaces (chord stays on the first piece), then group pieces
        # into whole words. Each word is one non-breaking unit so wrapping never splits a word,
        # even when a chord sits mid-word.
        segments = []
        for ch in chunks:
            pieces = re.findall(r'\S+|\s+', ch["text"]) or [""]
            for i, piece in enumerate(pieces):
                segments.append({"chord": ch["chord"] if i == 0 else "", "text": piece})
        words, cur = [], []
        for seg in segments:
            cur.append(seg)
            if seg["text"] and not seg["text"].strip():  # whitespace ends the current word
                words.append(cur)
                cur = []
        if cur:
            words.append(cur)

        whtml = []
        for word in words:
            chs = []
            for seg in word:
                # Empty text (e.g. a trailing chord) still needs a text line so the chord stays
                # on the chord row instead of dropping to the lyric baseline.
                text = _esc(seg["text"]) if seg["text"] else "&nbsp;"
                chs.append(
                    f'<span class="ch"><span class="c" data-chord="{_esc(seg["chord"])}">'
                    f'{_esc(seg["chord"])}</span>{text}</span>'
                )
            whtml.append(f'<span class="w">{"".join(chs)}</span>')
        out.append(f'<div class="line">{"".join(whtml)}</div>')
    return "\n".join(out)


_PAGE = """<!DOCTYPE html>
<html lang="cs">
  <head>
    <title>{{TITLE}}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#1b2021">
    <style>
html{background:#1b2021;}
body{background:#1b2021;font-family:'Courier New',monospace;color:#CFC7D2;overflow-x:hidden;margin:0;min-height:100vh;}
h1{color:#CFC7D2;margin:20px 20px 4px;}
h1 .hy{color:#FEB12C;}
.artist{color:#FEB12C;font-weight:bold;font-size:20px;margin:0 20px 12px;}
.bar{margin:0 20px 12px;display:flex;gap:8px;flex-wrap:wrap;}
.bar button{background:#1b2021;color:#FEB12C;border:2px solid #FEB12C;border-radius:6px;
  font-family:inherit;font-weight:bold;font-size:16px;padding:6px 12px;cursor:pointer;}
#song{margin:20px;font-size:16px;padding-bottom:80px;}
.line{margin:0 0 .4em;}
.br{height:.9em;}/* blank line in source = stanza break, clearly bigger than line gap */
.w{display:inline-block;vertical-align:bottom;white-space:pre;}/* whole word = one non-breaking unit */
.ch{display:inline-block;vertical-align:bottom;white-space:pre;}
.ch .c{display:block;color:#FEB12C;font-weight:bold;font-size:.8em;line-height:1;height:1.15em;}
.chordrow{margin:.3em 0;}
.chordrow .c{color:#FEB12C;font-weight:bold;display:inline-block;margin-right:1.5ch;}
a.back{position:fixed;right:16px;bottom:16px;background:#FEB12C;color:#1b2021;border-radius:8px;
  padding:10px 14px;font-family:'Courier New',monospace;font-weight:bold;text-decoration:none;opacity:.85;}
    </style>
  </head>
  <body>
    <h1>{{H1}}</h1>
    <p class="artist">{{ARTIST}}</p>
    <div class="bar">
      <button id="transDown" title="O půltón níž">&#9837; -1</button>
      <button id="transReset" title="Původní tónina">&#9838; 0</button>
      <button id="transUp" title="O půltón výš">&#9839; +1</button>
      <button id="fontDown" title="Menší písmo">A&minus;</button>
      <button id="fontUp" title="Větší písmo">A+</button>
    </div>
    <div id="song">
{{BODY}}
    </div>
    <a class="back" href="/">&larr; Seznam</a>
""" + r"""    <script>
    // Transpozice akordů (zná české značení: H = B, B = Bb)
    (function () {
      var SCALE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "B", "H"];
      var IDX = {"C":0,"C#":1,"DB":1,"D":2,"D#":3,"EB":3,"E":4,"FB":4,"F":5,"F#":6,
                 "GB":6,"G":7,"G#":8,"AB":8,"A":9,"A#":10,"B":10,"HB":10,"H":11,"CB":11};
      function one(tok, n) {
        var m = tok.match(/^([A-H][b#]?)(.*)$/);
        if (!m) return tok;
        var key = m[1].toUpperCase();
        if (!(key in IDX)) return tok;
        var rest = m[2].replace(/\/([A-H][b#]?)/, function (_, b) {
          var bk = b.toUpperCase();
          return (bk in IDX) ? "/" + SCALE[((IDX[bk] + n) % 12 + 12) % 12] : "/" + b;
        });
        return SCALE[((IDX[key] + n) % 12 + 12) % 12] + rest;
      }
      window.__shift = one;
      var off = 0, key = "trans:" + location.pathname;
      try { off = parseInt(localStorage.getItem(key) || "0", 10) || 0; } catch (e) {}
      function apply() {
        var els = document.querySelectorAll(".c[data-chord]");
        for (var i = 0; i < els.length; i++) {
          var orig = els[i].getAttribute("data-chord");
          els[i].textContent = orig ? one(orig, off) : "";
        }
        try { localStorage.setItem(key, String(off)); } catch (e) {}
      }
      function bump(d) { off = ((off + d) % 12 + 12) % 12; apply(); }
      document.getElementById("transUp").addEventListener("click", function () { bump(1); });
      document.getElementById("transDown").addEventListener("click", function () { bump(-1); });
      document.getElementById("transReset").addEventListener("click", function () { off = 0; apply(); });
      apply();
    })();
    </script>
    <script>
    // Uživatelská velikost písma (ukládá se globálně)
    (function () {
      var el = document.getElementById("song"), key = "fontpx";
      function get() { try { return parseInt(localStorage.getItem(key) || "16", 10) || 16; } catch (e) { return 16; } }
      function set(px) {
        px = Math.max(9, Math.min(40, px));
        el.style.fontSize = px + "px";
        try { localStorage.setItem(key, String(px)); } catch (e) {}
      }
      set(get());
      document.getElementById("fontUp").addEventListener("click", function () { set(get() + 1); });
      document.getElementById("fontDown").addEventListener("click", function () { set(get() - 1); });
    })();
    </script>
    <script>
    // Drží rozsvícenou obrazovku, dokud je píseň otevřená (hraní podle textu)
    if ('wakeLock' in navigator) {
      let zamek = null;
      const obnovZamek = () => {
        navigator.wakeLock.request('screen').then(z => { zamek = z; }).catch(() => {});
      };
      obnovZamek();
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') obnovZamek();
      });
    }
    </script>
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
      });
    }
    </script>
  </body>
</html>
"""


def _title_h1(title):
    """Title HTML with the last word in yellow (matches the original songbook style)."""
    title = title.strip()
    if not title:
        return ""
    head, _, last = title.rpartition(" ")
    if head:
        return _esc(head) + ' <span class="hy">' + _esc(last) + '</span>'
    return '<span class="hy">' + _esc(last) + '</span>'


def render_page(doc):
    """Parsed ChordPro doc -> full standalone HTML page string."""
    return (
        _PAGE
        .replace("{{TITLE}}", _esc(doc["title"]))
        .replace("{{H1}}", _title_h1(doc["title"]))
        .replace("{{ARTIST}}", _esc(doc["artist"]))
        .replace("{{BODY}}", render_song_body(doc["lines"]))
    )
