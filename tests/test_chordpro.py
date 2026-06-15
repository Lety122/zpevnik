import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import chordpro


def test_parse_directives_and_lines():
    text = "{title: Anděl}\n{artist: Karel Kryl}\n\n[D]Ahoj [Hm]světe\n"
    doc = chordpro.parse_pro(text)
    assert doc["title"] == "Anděl"
    assert doc["artist"] == "Karel Kryl"
    assert doc["lines"] == [
        {"type": "blank"},
        {"type": "lyric", "chunks": [
            {"chord": "D", "text": "Ahoj "},
            {"chord": "Hm", "text": "světe"},
        ]},
    ]


def test_parse_leading_text_before_chord():
    doc = chordpro.parse_pro("Z [D]kostela")
    assert doc["lines"][0]["chunks"] == [
        {"chord": "", "text": "Z "},
        {"chord": "D", "text": "kostela"},
    ]


def test_parse_chord_only_line():
    doc = chordpro.parse_pro("[D] [A7]")
    assert doc["lines"][0] == {"type": "chordonly", "chords": ["D", "A7"]}


def test_parse_chord_only_comma():
    doc = chordpro.parse_pro("[D, A7]")
    assert doc["lines"][0] == {"type": "chordonly", "chords": ["D", "A7"]}


def test_parse_plain_text_line():
    doc = chordpro.parse_pro("R: refrén")
    assert doc["lines"][0] == {"type": "lyric", "chunks": [{"chord": "", "text": "R: refrén"}]}


def test_render_lyric_chunk():
    doc = chordpro.parse_pro("[D]Ahoj [Hm]světe")
    h = chordpro.render_song_body(doc["lines"])
    # words are grouped; the syllable text no longer carries the trailing space
    assert '<span class="ch"><span class="c" data-chord="D">D</span>Ahoj</span>' in h
    assert '<span class="c" data-chord="Hm">Hm</span>světe' in h
    assert '<span class="w">' in h


def test_render_escapes_html():
    doc = chordpro.parse_pro("[D]a < b & c")
    h = chordpro.render_song_body(doc["lines"])
    assert "&lt;" in h and "&amp;" in h


def test_render_chordonly():
    doc = chordpro.parse_pro("[D] [A7]")
    h = chordpro.render_song_body(doc["lines"])
    assert 'class="chordrow"' in h
    assert 'data-chord="D"' in h and 'data-chord="A7"' in h


def test_render_leading_text_keeps_empty_chord_slot():
    doc = chordpro.parse_pro("Z [D]kostela")
    h = chordpro.render_song_body(doc["lines"])
    assert '<span class="c" data-chord=""></span>Z</span>' in h


def test_render_word_not_split_by_midword_chord():
    # a chord mid-word keeps the whole word inside one <span class="w"> (no break point)
    doc = chordpro.parse_pro("ne[G]umřelo")
    h = chordpro.render_song_body(doc["lines"])
    assert '<span class="w"><span class="ch"><span class="c" data-chord="">' in h
    assert h.count('<span class="w">') == 1  # single word -> single non-breaking unit


def test_render_page_has_essentials():
    doc = chordpro.parse_pro("{title: Anděl}\n{artist: Karel Kryl}\n[D]Ahoj")
    page = chordpro.render_page(doc)
    assert "<!DOCTYPE html>" in page and 'lang="cs"' in page
    assert "<title>Anděl</title>" in page
    assert '<span class="hy">Anděl</span>' in page  # single-word title -> all yellow
    assert "Karel Kryl" in page
    assert 'id="transUp"' in page and 'id="transDown"' in page
    assert 'id="fontUp"' in page and 'id="fontDown"' in page and 'id="fontReset"' in page
    assert 'href="/"' in page
    assert "serviceWorker" in page and "wakeLock" in page
    assert 'data-chord="D"' in page


def test_title_last_word_yellow():
    doc = chordpro.parse_pro("{title: Na hotelu v Olomouci}\n{artist: X}\n[C]y")
    page = chordpro.render_page(doc)
    assert 'Na hotelu v <span class="hy">Olomouci</span>' in page


def test_render_page_escapes_title():
    doc = chordpro.parse_pro("{title: A & B}\n{artist: X}\n[C]y")
    page = chordpro.render_page(doc)
    assert "<title>A &amp; B</title>" in page


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("ALL PASS")
