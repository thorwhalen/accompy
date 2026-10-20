"""ChordPro sections and the songleaf Song -> ChordSequence converter (no songleaf needed)."""

from types import SimpleNamespace as NS

import pytest

from accompy import ChordSequence, song_to_chord_sequence
from accompy.chord_parsers import parse_chordpro


def _song():
    text = "Hello there friend\nGoodbye now\n\nLa la la"
    return NS(
        text=text,
        annotations=[
            NS(kind="section", start=0, end=30, body={"label": "Verse"}),
            NS(kind="section", start=32, end=40, body={"label": "Chorus"}),
            NS(kind="chord", start=0, end=0, body={"symbol": "C"}),
            NS(kind="chord", start=6, end=6, body={"symbol": "G"}),
            NS(kind="chord", start=19, end=19, body={"symbol": "Am"}),
            NS(kind="chord", start=32, end=32, body={"symbol": "F"}),
        ],
        meta={"title": "Hi", "key": "G", "tempo": 90},
    )


def test_default_is_one_bar_per_chord():
    cs = song_to_chord_sequence(_song())
    assert cs.chords == [("C", 4.0), ("G", 4.0), ("Am", 4.0), ("F", 4.0)]
    assert (cs.title, cs.key, cs.tempo) == ("Hi", "G", 90)
    assert cs.sections == [("Verse", 0, 3), ("Chorus", 3, 4)]
    assert cs.section_chords("chorus") == [("F", 4.0)]


def test_bars_per_line_shares_the_line_between_its_chords():
    cs = song_to_chord_sequence(_song(), bars_per_line=2)
    assert cs.chords == [("C", 4.0), ("G", 4.0), ("Am", 8.0), ("F", 8.0)]


def test_beats_per_chord_is_fixed():
    cs = song_to_chord_sequence(_song(), beats_per_chord=2, beats_per_bar=3)
    assert cs.durations == [2.0] * 4 and cs.time_signature == (3, 4)


@pytest.mark.parametrize("kwargs", [{"bars_per_line": 1, "beats_per_chord": 1}, {"bars_per_line": 0}])
def test_bad_heuristics_are_refused(kwargs):
    with pytest.raises(ValueError):
        song_to_chord_sequence(_song(), **kwargs)


def test_a_real_songleaf_song_converts():
    songleaf_model = pytest.importorskip("songleaf.model")
    song = songleaf_model.Song(
        "Hello there\nGoodbye now",
        [songleaf_model.section(0, 23, "Verse"), songleaf_model.chord(0, "C"), songleaf_model.chord(12, "G/B")],
        meta={"title": "T"},
    )
    cs = song_to_chord_sequence(song, bars_per_line=1)
    assert cs.chords == [("C", 4.0), ("G/B", 4.0)] and cs.sections == [("Verse", 0, 2)]
    assert isinstance(cs, ChordSequence)


def test_chordpro_keeps_sections_and_a_bare_chorus_marker_is_not_a_chord():
    cs = parse_chordpro(
        "{title: T}\n{start_of_verse: Verse 1}\n[Am]la [G]la\n{end_of_verse}\n[Chorus]\n[C]sing [F]out\n"
        "{comment: Bridge}\n[Dm]oh"
    )
    assert cs.symbols == ["Am", "G", "C", "F", "Dm"]
    assert cs.sections == [("Verse 1", 0, 2), ("Chorus", 2, 4), ("Bridge", 4, 5)]
    assert cs.title == "T"


def test_chordpro_without_sections_is_unchanged():
    cs = parse_chordpro("[Am]Hello [G]world [C]goodbye")
    assert cs.symbols == ["Am", "G", "C"] and cs.sections == []
