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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("ALL PASS")
