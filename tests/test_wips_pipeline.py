"""Tests for accompy.wips.pipeline — high-level API."""

import os

import numpy as np
import pytest

from accompy.wips.pipeline import (
    chords_to_audio,
    chords_to_midi,
    chords_to_notes,
    chords_to_sequence,
    list_available_converters,
    midi_to_audio,
)
from accompy.wips.types import AudioData, ChordSequence, MidiData, NoteSequence


class TestChordsToSequence:
    def test_basic(self):
        cs = chords_to_sequence("| Dm7 | G7 | Cmaj7 |")
        assert isinstance(cs, ChordSequence)
        assert cs.symbols == ["Dm7", "G7", "Cmaj7"]

    def test_with_tempo(self):
        cs = chords_to_sequence("C Am F G", tempo=180)
        assert cs.tempo == 180

    def test_with_metadata(self):
        cs = chords_to_sequence(
            "| C | Am |", title="Test", key="G", time_signature=(3, 4)
        )
        assert cs.title == "Test"
        assert cs.key == "G"


class TestChordsToNotes:
    def test_from_string(self):
        ns = chords_to_notes("| C | Am |")
        assert isinstance(ns, NoteSequence)
        assert len(ns) == 2

    def test_from_chord_sequence(self):
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
        ns = chords_to_notes(cs)
        assert len(ns) == 2

    @pytest.mark.parametrize("resolver", ["pychord", "music21", "mingus", "tonal"])
    def test_all_resolvers(self, resolver):
        ns = chords_to_notes("| C | Am | F | G |", resolver=resolver)
        assert len(ns) == 4
        # All notes in valid MIDI range
        for notes, _ in ns:
            assert all(0 <= n <= 127 for n in notes)


class TestChordsToMidi:
    def test_basic(self):
        md = chords_to_midi("| C | Am | F | G |")
        assert isinstance(md, MidiData)
        assert md.to_bytes()[:4] == b"MThd"

    def test_with_explicit_backends(self):
        md = chords_to_midi(
            "| Dm7 | G7 |",
            resolver="music21",
            midi_gen="mido",
        )
        assert md.to_bytes()[:4] == b"MThd"

    def test_write_to_file(self, tmp_path):
        path = str(tmp_path / "test.mid")
        md = chords_to_midi("| C | G |", output_path=path)
        with open(path, "rb") as f:
            assert f.read(4) == b"MThd"

    def test_from_chord_sequence(self):
        cs = ChordSequence(
            [("Cmaj7", 4.0), ("Fmaj7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)],
            tempo=160,
        )
        md = chords_to_midi(cs)
        assert md.to_bytes()[:4] == b"MThd"


class TestChordsToAudio:
    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth not available",
    )
    def test_basic(self):
        audio = chords_to_audio("| C | Am | F | G |")
        assert isinstance(audio, AudioData)
        assert isinstance(audio.waveform, np.ndarray)
        assert len(audio.waveform) > 0
        assert audio.sr == 44100

    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth not available",
    )
    def test_write_to_file(self, tmp_path):
        path = str(tmp_path / "test.wav")
        audio = chords_to_audio("| C | G |", output_path=path)
        with open(path, "rb") as f:
            assert f.read(4) == b"RIFF"


class TestMidiToAudio:
    @pytest.mark.skipif(
        not os.path.exists(
            os.path.expanduser("~/.fluidsynth/default_sound_font.sf2")
        ),
        reason="FluidSynth not available",
    )
    def test_basic(self):
        md = chords_to_midi("| C | Am |")
        audio = midi_to_audio(md)
        assert isinstance(audio, AudioData)
        assert len(audio.waveform) > 0


class TestListAvailableConverters:
    def test_returns_all_stages(self):
        info = list_available_converters()
        assert "parsers" in info
        assert "resolvers" in info
        assert "midi_generators" in info
        assert "audio_renderers" in info

    def test_has_expected_resolvers(self):
        info = list_available_converters()
        assert set(info["resolvers"]) >= {"pychord", "music21", "mingus", "tonal"}

    def test_has_expected_midi_gens(self):
        info = list_available_converters()
        assert set(info["midi_generators"]) >= {"pretty_midi", "midiutil", "mido"}


class TestRealWorldProgressions:
    """Test with real jazz/pop chord progressions."""

    @pytest.mark.parametrize(
        "name,chords",
        [
            ("ii-V-I", "| Dm7 | G7 | Cmaj7 |"),
            ("blues", "| C7 | C7 | C7 | C7 | F7 | F7 | C7 | C7 | G7 | F7 | C7 | G7 |"),
            ("rhythm_changes_A", "| Bb | Gm | Cm7 | F7 | Dm7 | G7 | Cm7 | F7 |"),
            ("autumn_leaves_A", "| Am7 | D7 | Gmaj7 | Cmaj7 | F#m7b5 | B7 | Em | Em |"),
            ("pop_I_V_vi_IV", "| C | G | Am | F |"),
        ],
    )
    def test_generates_midi(self, name, chords):
        md = chords_to_midi(chords)
        assert md.to_bytes()[:4] == b"MThd", f"Failed for {name}"
