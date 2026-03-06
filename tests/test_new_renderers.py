"""Tests for new renderers: DawDreamer, MusicGen-Chord, MMA."""

import pytest

from accompy.converters import ChordSequence, MidiData, AudioData, converter


# ---------------------------------------------------------------------------
# DawDreamer audio renderer
# ---------------------------------------------------------------------------


class TestDawDreamer:
    def test_registered(self):
        """DawDreamer should be registered as a MidiData->AudioData converter."""
        names = converter.list_converters(MidiData, AudioData)
        assert "dawdreamer" in names

    def test_import_error_message(self):
        """Should raise ImportError with install instructions if not installed."""
        try:
            import dawdreamer  # noqa: F401
            pytest.skip("dawdreamer is installed")
        except ImportError:
            pass

        from accompy.audio_renderers import midi_to_audio_dawdreamer
        from accompy.converters import NoteSequence

        ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
        md = converter.get(NoteSequence, MidiData, "pretty_midi")(ns)

        with pytest.raises(ImportError, match="dawdreamer"):
            midi_to_audio_dawdreamer(md)


# ---------------------------------------------------------------------------
# MMA MIDI generator
# ---------------------------------------------------------------------------


class TestMMA:
    def test_registered(self):
        """MMA should be registered as a ChordSequence->MidiData converter."""
        names = converter.list_converters(ChordSequence, MidiData)
        assert "mma" in names

    def test_runtime_error_if_not_installed(self):
        """Should raise RuntimeError if mma CLI is not on PATH."""
        import shutil
        if shutil.which("mma"):
            pytest.skip("MMA is installed")

        from accompy.midi_generators import chordseq_to_midi_mma

        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
        with pytest.raises(RuntimeError, match="MMA"):
            chordseq_to_midi_mma(cs)

    def test_mma_format_generation(self):
        """Test that MMA text format is generated correctly."""
        from accompy.base import AccompanimentConfig
        from accompy.main import _score_to_mma

        cs = ChordSequence(
            [("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)],
            tempo=140,
        )
        score = cs.to_score()
        config = AccompanimentConfig(style="swing", tempo=140)
        mma_text = _score_to_mma(score, config)

        assert "Tempo 140" in mma_text
        assert "Groove Swing" in mma_text
        # Score measures contain chord symbols
        assert any("D-7" in line or "Dm7" in line for line in mma_text.split("\n"))


# ---------------------------------------------------------------------------
# MusicGen-Chord audio renderer
# ---------------------------------------------------------------------------


class TestMusicGenChord:
    def test_registered(self):
        """MusicGen-Chord should be registered as a ChordSequence->AudioData converter."""
        names = converter.list_converters(ChordSequence, AudioData)
        assert "musicgen_chord" in names

    def test_import_error_message(self):
        """Should raise ImportError with install instructions if not installed."""
        try:
            import audiocraft  # noqa: F401
            pytest.skip("audiocraft is installed")
        except ImportError:
            pass

        from accompy.audio_renderers import chordseq_to_audio_musicgen

        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
        with pytest.raises(ImportError, match="audiocraft"):
            chordseq_to_audio_musicgen(cs)
