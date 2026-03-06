"""Tests for accompy.converters — core types and converter registry."""

import numpy as np
import pytest

from accompy.converters import (
    AudioData,
    ChordSequence,
    ChordSheet,
    ConverterRegistry,
    MidiData,
    NoteSequence,
    convert,
    converter,
)


# ---------------------------------------------------------------------------
# ChordSequence tests
# ---------------------------------------------------------------------------


class TestChordSequence:
    def test_basic_creation(self):
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 8.0)])
        assert len(cs) == 3
        assert cs[0] == ("Dm7", 4.0)
        assert cs.total_beats == 16.0

    def test_symbols_and_durations(self):
        cs = ChordSequence([("Am", 2.0), ("F", 2.0)])
        assert cs.symbols == ["Am", "F"]
        assert cs.durations == [2.0, 2.0]

    def test_iteration(self):
        events = [("C", 4.0), ("G", 4.0)]
        cs = ChordSequence(events)
        assert list(cs) == events

    def test_metadata(self):
        cs = ChordSequence(
            [("C", 4.0)],
            title="Test",
            key="G",
            tempo=140,
            time_signature=(3, 4),
        )
        assert cs.title == "Test"
        assert cs.key == "G"
        assert cs.tempo == 140
        assert cs.time_signature == (3, 4)

    def test_empty(self):
        cs = ChordSequence([])
        assert len(cs) == 0
        assert cs.total_beats == 0.0

    def test_to_score(self):
        """ChordSequence can be converted to a Score."""
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
        score = cs.to_score()
        assert len(score) == 2

    def test_to_score_round_trip(self):
        """ChordSequence -> Score -> ChordSequence preserves chord count."""
        cs = ChordSequence(
            [("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)],
            tempo=140,
        )
        score = cs.to_score()
        cs2 = score.to_chord_sequence(tempo=140)
        assert len(cs2) == len(cs)


# ---------------------------------------------------------------------------
# NoteSequence tests
# ---------------------------------------------------------------------------


class TestNoteSequence:
    def test_basic(self):
        ns = NoteSequence([([60, 64, 67], 4.0), ([62, 65, 69], 4.0)])
        assert len(ns) == 2
        assert ns[0] == ([60, 64, 67], 4.0)
        assert ns.total_beats == 8.0

    def test_iteration(self):
        events = [([48, 52, 55], 2.0)]
        ns = NoteSequence(events)
        assert list(ns) == events


# ---------------------------------------------------------------------------
# MidiData tests
# ---------------------------------------------------------------------------


class TestMidiData:
    def test_from_bytes(self):
        md = MidiData(bytes_=b"MThd\x00\x00\x00\x06")
        assert md.has_bytes
        assert not md.has_pretty_midi

    def test_to_bytes_from_bytes(self):
        raw = b"test_midi_data"
        md = MidiData(bytes_=raw)
        assert md.to_bytes() == raw

    def test_empty_raises(self):
        md = MidiData()
        with pytest.raises(ValueError, match="no content"):
            md.to_bytes()

    def test_write(self, tmp_path):
        md = MidiData(bytes_=b"MThd_fake")
        path = str(tmp_path / "test.mid")
        result = md.write(path)
        assert result == path
        with open(path, "rb") as f:
            assert f.read() == b"MThd_fake"


# ---------------------------------------------------------------------------
# AudioData tests
# ---------------------------------------------------------------------------


class TestAudioData:
    def test_duration(self):
        ad = AudioData(waveform=np.zeros(44100), sr=44100)
        assert ad.duration_seconds == 1.0

    def test_to_wav_bytes(self):
        ad = AudioData(waveform=np.sin(np.linspace(0, 1, 1000)), sr=44100)
        wav = ad.to_wav_bytes()
        assert wav[:4] == b"RIFF"
        assert len(wav) > 44  # WAV header + data

    def test_write(self, tmp_path):
        ad = AudioData(waveform=np.zeros(100), sr=44100)
        path = str(tmp_path / "test.wav")
        result = ad.write(path)
        assert result == path
        with open(path, "rb") as f:
            assert f.read(4) == b"RIFF"

    def test_silent_audio(self):
        ad = AudioData(waveform=np.zeros(100), sr=44100)
        wav = ad.to_wav_bytes()
        assert len(wav) > 0  # Should not crash on all-zeros


# ---------------------------------------------------------------------------
# ConverterRegistry tests
# ---------------------------------------------------------------------------


class TestConverterRegistry:
    def test_register_and_get(self):
        reg = ConverterRegistry()
        reg.register(str, int, int, name="builtin")
        assert reg[str, int]("42") == 42

    def test_first_registered_is_default(self):
        reg = ConverterRegistry()
        reg.register(str, int, lambda s: int(s), name="first")
        reg.register(str, int, lambda s: int(s) * 2, name="second")
        assert reg[str, int]("5") == 5  # first is default

    def test_set_default(self):
        reg = ConverterRegistry()
        reg.register(str, int, lambda s: int(s), name="normal")
        reg.register(str, int, lambda s: int(s) * 10, name="times10")
        reg.set_default(str, int, "times10")
        assert reg[str, int]("3") == 30

    def test_get_by_name(self):
        reg = ConverterRegistry()
        reg.register(str, int, lambda s: int(s), name="normal")
        reg.register(str, int, lambda s: int(s) + 100, name="plus100")
        assert reg.get(str, int, "plus100")("5") == 105

    def test_list_converters(self):
        reg = ConverterRegistry()
        reg.register(str, int, int, name="a")
        reg.register(str, int, int, name="b")
        assert reg.list_converters(str, int) == ["a", "b"]

    def test_list_pairs(self):
        reg = ConverterRegistry()
        reg.register(str, int, int, name="a")
        reg.register(int, str, str, name="b")
        pairs = reg.list_pairs()
        assert ("str", "int") in pairs
        assert ("int", "str") in pairs

    def test_missing_pair_raises(self):
        reg = ConverterRegistry()
        with pytest.raises(KeyError):
            reg[str, int]

    def test_missing_name_raises(self):
        reg = ConverterRegistry()
        reg.register(str, int, int, name="a")
        with pytest.raises(KeyError, match="No converter named"):
            reg.get(str, int, "nonexistent")

    def test_is_default_flag(self):
        reg = ConverterRegistry()
        reg.register(str, int, lambda s: 0, name="first")
        reg.register(str, int, lambda s: 1, name="second", is_default=True)
        assert reg[str, int]("x") == 1


# ---------------------------------------------------------------------------
# convert() convenience function tests
# ---------------------------------------------------------------------------


class TestConvert:
    def test_basic_convert(self):
        """Test convert() uses the global registry."""
        converter.register(
            str,
            list,
            lambda s: list(s),
            name="_test_str_to_list",
        )
        result = convert("abc", list)
        assert result == ["a", "b", "c"]

    def test_convert_via_named(self):
        converter.register(
            str, list, lambda s: list(s), name="_test_default"
        )
        converter.register(
            str,
            list,
            lambda s: list(reversed(s)),
            name="_test_reversed",
        )
        result = convert("abc", list, via="_test_reversed")
        assert result == ["c", "b", "a"]
