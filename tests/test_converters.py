"""Tests for accompy converter modules.

Tests chord parsers, chord resolvers, MIDI generators, and audio renderers.
"""

import os

import numpy as np
import pytest

from accompy.converters import (
    AudioData,
    ChordSequence,
    ChordSheet,
    MidiData,
    NoteSequence,
    convert,
    converter,
)


# ===================================================================
# Chord Parsers: ChordSheet / str -> ChordSequence
# ===================================================================


class TestPlainTextParser:
    def test_bar_line_format(self):
        cs = convert(ChordSheet("| Dm7 | G7 | Cmaj7 |"), ChordSequence)
        assert cs.symbols == ["Dm7", "G7", "Cmaj7"]
        assert cs.durations == [4.0, 4.0, 4.0]

    def test_space_separated(self):
        cs = convert(ChordSheet("C Am F G"), ChordSequence)
        assert len(cs) == 4
        assert cs.symbols == ["C", "Am", "F", "G"]

    def test_multi_chord_bar(self):
        cs = convert(ChordSheet("| C Am | F G |"), ChordSequence)
        assert cs.symbols == ["C", "Am", "F", "G"]
        assert cs.durations == [2.0, 2.0, 2.0, 2.0]

    def test_repeat_marker(self):
        cs = convert(ChordSheet("| C | % | G |"), ChordSequence)
        assert cs.symbols == ["C", "C", "G"]

    def test_str_also_works(self):
        """str type is also registered for convenience."""
        cs = convert("| A | B |", ChordSequence)
        assert len(cs) == 2


class TestChordProParser:
    def test_basic_chordpro(self):
        from accompy.chord_parsers import parse_chordpro

        cs = parse_chordpro("[Am]Hello [G]world [C]goodbye")
        assert cs.symbols == ["Am", "G", "C"]

    def test_metadata_extraction(self):
        from accompy.chord_parsers import parse_chordpro

        text = "{title: My Song}\n{key: G}\n{tempo: 140}\n[G]La [C]la"
        cs = parse_chordpro(text)
        assert cs.title == "My Song"
        assert cs.key == "G"
        assert cs.tempo == 140


class TestMusicGenChordParser:
    def test_simple_format(self):
        from accompy.chord_parsers import parse_musicgen_chord_format

        cs = parse_musicgen_chord_format("C D:min G:7 C")
        assert cs.symbols == ["C", "D:min", "G:7", "C"]
        assert all(d == 4.0 for d in cs.durations)

    def test_comma_separated_within_bar(self):
        from accompy.chord_parsers import parse_musicgen_chord_format

        cs = parse_musicgen_chord_format("C:maj,G:maj E:min")
        assert len(cs) == 3
        assert cs.durations == [2.0, 2.0, 4.0]


class TestAutoDetect:
    def test_detects_bar_lines(self):
        cs = convert(ChordSheet("| C | Am |"), ChordSequence)
        assert cs.symbols == ["C", "Am"]

    def test_detects_chordpro(self):
        cs = convert(ChordSheet("[Am]Hello [G]world"), ChordSequence)
        assert cs.symbols == ["Am", "G"]

    def test_detects_musicgen(self):
        from accompy.chord_parsers import parse_chord_sheet

        cs = parse_chord_sheet("C:maj D:min G:7")
        assert len(cs) == 3


# ===================================================================
# Chord Resolvers: ChordSequence -> NoteSequence
# ===================================================================


SIMPLE_CS = ChordSequence(
    [("C", 4.0), ("Am", 4.0), ("G7", 4.0)],
    tempo=120,
)


class TestPychordResolver:
    def test_resolves_basic_chords(self):
        ns = converter.get(ChordSequence, NoteSequence, "pychord")(SIMPLE_CS)
        assert len(ns) == 3
        c_notes = ns[0][0]
        pcs = {n % 12 for n in c_notes}
        assert 0 in pcs  # C
        assert 4 in pcs  # E
        assert 7 in pcs  # G

    def test_preserves_durations(self):
        ns = converter.get(ChordSequence, NoteSequence, "pychord")(SIMPLE_CS)
        assert ns[0][1] == 4.0


class TestMusic21Resolver:
    def test_resolves_basic_chords(self):
        ns = converter.get(ChordSequence, NoteSequence, "music21")(SIMPLE_CS)
        assert len(ns) == 3
        assert all(len(notes) >= 3 for notes, _ in ns)

    def test_handles_complex_chords(self):
        cs = ChordSequence([("Dm7b5", 4.0), ("G7b9", 4.0)])
        ns = converter.get(ChordSequence, NoteSequence, "music21")(cs)
        assert len(ns) == 2


class TestMingusResolver:
    def test_resolves_basic_chords(self):
        ns = converter.get(ChordSequence, NoteSequence, "mingus")(SIMPLE_CS)
        assert len(ns) == 3

    def test_c_major_has_correct_pitches(self):
        cs = ChordSequence([("Cmaj7", 4.0)])
        ns = converter.get(ChordSequence, NoteSequence, "mingus")(cs)
        midi_notes = ns[0][0]
        pcs = {n % 12 for n in midi_notes}
        assert {0, 4, 7, 11} == pcs


class TestTonalResolver:
    def test_resolves_basic_chords(self):
        ns = converter.get(ChordSequence, NoteSequence, "tonal")(SIMPLE_CS)
        assert len(ns) == 3


class TestResolverConsistency:
    """Verify all resolvers agree on pitch classes for common chords."""

    @pytest.mark.parametrize("resolver_name", ["pychord", "music21", "mingus", "tonal"])
    def test_c_major_pitch_classes(self, resolver_name):
        cs = ChordSequence([("C", 4.0)])
        ns = converter.get(ChordSequence, NoteSequence, resolver_name)(cs)
        pcs = {n % 12 for n in ns[0][0]}
        assert 0 in pcs, f"{resolver_name} missing C"
        assert 4 in pcs, f"{resolver_name} missing E"
        assert 7 in pcs, f"{resolver_name} missing G"

    @pytest.mark.parametrize("resolver_name", ["pychord", "music21", "mingus", "tonal"])
    def test_returns_midi_range(self, resolver_name):
        """All notes should be valid MIDI (0-127)."""
        cs = ChordSequence([("Am7", 4.0), ("Dm7", 4.0)])
        ns = converter.get(ChordSequence, NoteSequence, resolver_name)(cs)
        for midi_notes, _ in ns:
            assert all(0 <= n <= 127 for n in midi_notes), (
                f"{resolver_name} produced out-of-range notes: {midi_notes}"
            )


# ===================================================================
# MIDI Generators: NoteSequence -> MidiData
# ===================================================================


SIMPLE_NS = NoteSequence(
    [([60, 64, 67], 4.0), ([57, 60, 64], 4.0)],
    tempo=120,
)


class TestPrettyMidiGenerator:
    def test_generates_midi(self):
        md = converter.get(NoteSequence, MidiData, "pretty_midi")(SIMPLE_NS)
        assert md.has_pretty_midi

    def test_round_trip_notes(self):
        md = converter.get(NoteSequence, MidiData, "pretty_midi")(SIMPLE_NS)
        pm = md.to_pretty_midi()
        assert len(pm.instruments) == 1
        assert len(pm.instruments[0].notes) == 6  # 3 notes * 2 chords

    def test_to_bytes(self):
        md = converter.get(NoteSequence, MidiData, "pretty_midi")(SIMPLE_NS)
        b = md.to_bytes()
        assert b[:4] == b"MThd"


class TestMidiUtilGenerator:
    def test_generates_bytes(self):
        md = converter.get(NoteSequence, MidiData, "midiutil")(SIMPLE_NS)
        assert md.has_bytes
        assert md.to_bytes()[:4] == b"MThd"


class TestMidoGenerator:
    def test_generates_bytes(self):
        md = converter.get(NoteSequence, MidiData, "mido")(SIMPLE_NS)
        assert md.has_bytes
        assert md.to_bytes()[:4] == b"MThd"


class TestMidiGeneratorConsistency:
    """All MIDI generators should produce valid MIDI bytes."""

    @pytest.mark.parametrize("gen_name", ["pretty_midi", "midiutil", "mido"])
    def test_produces_valid_midi_header(self, gen_name):
        md = converter.get(NoteSequence, MidiData, gen_name)(SIMPLE_NS)
        assert md.to_bytes()[:4] == b"MThd"

    @pytest.mark.parametrize("gen_name", ["pretty_midi", "midiutil", "mido"])
    def test_writes_to_file(self, gen_name, tmp_path):
        md = converter.get(NoteSequence, MidiData, gen_name)(SIMPLE_NS)
        path = str(tmp_path / f"test_{gen_name}.mid")
        md.write(path)
        with open(path, "rb") as f:
            assert f.read(4) == b"MThd"


# ===================================================================
# Shortcut converters: ChordSequence -> MidiData
# ===================================================================


class TestChordSeqToMidiShortcuts:
    def test_pychord_pretty_midi(self):
        md = converter.get(ChordSequence, MidiData, "pychord+pretty_midi")(SIMPLE_CS)
        assert md.to_bytes()[:4] == b"MThd"

    def test_tonal_midiutil(self):
        md = converter.get(ChordSequence, MidiData, "tonal+midiutil")(SIMPLE_CS)
        assert md.to_bytes()[:4] == b"MThd"

    def test_builtin_accompaniment(self):
        """Test the builtin pattern-based accompaniment converter."""
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
        md = converter.get(ChordSequence, MidiData, "builtin_accompaniment")(cs)
        assert md.to_bytes()[:4] == b"MThd"
        assert len(md.to_bytes()) > 100  # Should be a substantial MIDI file


# ===================================================================
# Audio Renderers: MidiData -> AudioData
# ===================================================================


@pytest.fixture
def simple_midi_data():
    """Create a simple MidiData for audio rendering tests."""
    md = converter.get(NoteSequence, MidiData, "pretty_midi")(SIMPLE_NS)
    return md


class TestFluidSynthRenderer:
    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth SoundFont not available",
    )
    def test_renders_audio(self, simple_midi_data):
        audio = converter.get(MidiData, AudioData, "fluidsynth")(simple_midi_data)
        assert isinstance(audio.waveform, np.ndarray)
        assert len(audio.waveform) > 0
        assert audio.sr == 44100


class TestPrettyMidiFluidSynthRenderer:
    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth SoundFont not available",
    )
    def test_renders_audio(self, simple_midi_data):
        audio = converter.get(MidiData, AudioData, "pretty_midi")(simple_midi_data)
        assert isinstance(audio.waveform, np.ndarray)
        assert len(audio.waveform) > 0


# ===================================================================
# End-to-end: str -> ChordSequence -> NoteSequence -> MidiData -> AudioData
# ===================================================================


class TestEndToEnd:
    def test_str_to_midi(self):
        """Full pipeline from string to MIDI."""
        cs = convert("| Dm7 | G7 | Cmaj7 |", ChordSequence)
        md = converter[ChordSequence, MidiData](cs)
        assert md.to_bytes()[:4] == b"MThd"

    def test_pipeline_step_by_step(self):
        """Each step of the pipeline produces the expected type."""
        cs = convert("| Am | Dm | G | C |", ChordSequence)
        assert isinstance(cs, ChordSequence)
        assert len(cs) == 4

        ns = converter[ChordSequence, NoteSequence](cs)
        assert isinstance(ns, NoteSequence)
        assert len(ns) == 4

        md = converter[NoteSequence, MidiData](ns)
        assert isinstance(md, MidiData)

    def test_list_all_registered_converters(self):
        """Verify all expected converter pairs are registered."""
        pairs = converter.list_pairs()
        assert ("ChordSheet", "ChordSequence") in pairs or ("str", "ChordSequence") in pairs
        assert ("ChordSequence", "NoteSequence") in pairs
        assert ("NoteSequence", "MidiData") in pairs
        assert ("MidiData", "AudioData") in pairs
        assert ("ChordSequence", "MidiData") in pairs
        assert ("ChordSequence", "AudioData") in pairs

    def test_list_resolver_names(self):
        names = converter.list_converters(ChordSequence, NoteSequence)
        assert "pychord" in names
        assert "music21" in names
        assert "mingus" in names
        assert "tonal" in names

    def test_list_midi_gen_names(self):
        names = converter.list_converters(NoteSequence, MidiData)
        assert "pretty_midi" in names
        assert "midiutil" in names
        assert "mido" in names

    def test_builtin_accompaniment_in_list(self):
        names = converter.list_converters(ChordSequence, MidiData)
        assert "builtin_accompaniment" in names

    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth SoundFont not available",
    )
    def test_full_pipeline_to_audio(self, tmp_path):
        """Full pipeline from chord string to WAV file."""
        cs = convert("| C | Am | F | G |", ChordSequence)
        ns = converter[ChordSequence, NoteSequence](cs)
        md = converter[NoteSequence, MidiData](ns)
        audio = converter[MidiData, AudioData](md)

        assert audio.duration_seconds > 0
        path = str(tmp_path / "test.wav")
        audio.write(path)
        with open(path, "rb") as f:
            assert f.read(4) == b"RIFF"
