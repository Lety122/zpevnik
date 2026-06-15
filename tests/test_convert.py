import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import convert_to_chordpro as conv


def test_merge_chord_line_into_lyric():
    # "A" at col 0, "B" at col 4
    assert conv.merge("A   B", "0123456789") == "[A]0123[B]456789"


def test_chords_past_lyric_end_appended():
    # "A" at col 0, "B7" at col 5; lyric only 4 chars
    assert conv.merge("A    B7", "Ahoj") == "[A]Ahoj [B7]"


def test_extract_title_artist():
    src = ('<title>Anděl</title>...'
           '<p><b><pre class="yellow" style="font-size: 20px;">Karel Kryl</pre></b></p>')
    assert conv.extract_title(src) == "Anděl"
    assert conv.extract_artist(src) == "Karel Kryl"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("ALL PASS")
