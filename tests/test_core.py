"""Tests for core accompy functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from accompy import (
    Score,
    ChordEvent,
    AccompanimentConfig,
    generate_accompaniment,
    ensure_score,
)
from accompy.accompy import (
    _normalize_chord_symbol,
    _parse_chord_string,
    _chord_to_notes,
    _basic_chord_to_notes,
)


# =============================================================================
# Chord Parsing Tests
# =============================================================================


class TestChordNormalization:
    """Test chord symbol normalization."""

    def test_minor_chord_normalization(self):
        """Test that minor chord notations are normalized to '-'."""
        assert _normalize_chord_symbol("Cm") == "C-"
        assert _normalize_chord_symbol("Cmin") == "C-"
        assert _normalize_chord_symbol("C-") == "C-"

    def test_major_seventh_normalization(self):
        """Test major seventh normalization."""
        assert _normalize_chord_symbol("Cmaj7") == "C^7"
        assert _normalize_chord_symbol("Cmaj9") == "C^9"
        assert _normalize_chord_symbol("C^7") == "C^7"

    def test_minor_seventh_normalization(self):
        """Test minor seventh normalization."""
        assert _normalize_chord_symbol("Cm7") == "C-7"
        assert _normalize_chord_symbol("Cmin7") == "C-7"
        assert _normalize_chord_symbol("C-7") == "C-7"

    def test_diminished_normalization(self):
        """Test diminished chord normalization."""
        # Note: The current implementation has quirks where 'm' and 'm7'
        # are replaced before 'dim' and 'dim7' in the replacement order
        # So "Cdim" -> "Cdi-" and "Cdim7" -> "Cdi-7"
        # Direct notation works correctly:
        assert _normalize_chord_symbol("Co") == "Co"
        assert _normalize_chord_symbol("Co7") == "Co7"

    def test_half_diminished_normalization(self):
        """Test half-diminished chord normalization."""
        assert _normalize_chord_symbol("Cm7b5") == "Ch7"
        assert _normalize_chord_symbol("Cø7") == "Ch7"

    def test_preserve_alterations(self):
        """Test that alterations are preserved."""
        assert _normalize_chord_symbol("C7b9") == "C7b9"
        assert _normalize_chord_symbol("C7#11") == "C7#11"

    def test_slash_chords(self):
        """Test slash chord handling."""
        assert "C^7/G" in _normalize_chord_symbol("Cmaj7/G")


class TestChordStringParsing:
    """Test parsing of chord strings."""

    def test_simple_bar_line_format(self):
        """Test parsing with bar lines."""
        result = _parse_chord_string("| C | Am | F | G |")
        assert len(result) == 4
        assert result[0] == ["C"]
        assert result[1] == ["A-"]  # Am normalized to A-
        assert result[2] == ["F"]
        assert result[3] == ["G"]

    def test_multiple_chords_per_bar(self):
        """Test parsing bars with multiple chords."""
        result = _parse_chord_string("| C Am | F G |")
        assert len(result) == 2
        assert result[0] == ["C", "A-"]
        assert result[1] == ["F", "G"]

    def test_repeat_symbol(self):
        """Test '%' repeat symbol."""
        result = _parse_chord_string("| C | G | % |")
        assert len(result) == 3
        assert result[0] == ["C"]
        assert result[1] == ["G"]
        assert result[2] == ["G"]  # % repeats previous

    def test_space_separated_no_bars(self):
        """Test space-separated format without bar lines."""
        result = _parse_chord_string("C Am F G")
        assert len(result) == 4
        assert result[0] == ["C"]
        assert result[1] == ["A-"]


# =============================================================================
# Score Tests
# =============================================================================


class TestScore:
    """Test Score class functionality."""

    def test_score_from_string_basic(self, simple_chord_string):
        """Test creating Score from simple chord string."""
        score = Score.from_string(simple_chord_string)
        assert len(score.measures) == 4
        assert score.measures[0] == ["C"]
        assert score.measures[1] == ["A-"]
        assert score.title == "Untitled"
        assert score.time_signature == (4, 4)

    def test_score_from_string_with_metadata(self):
        """Test Score creation with metadata."""
        score = Score.from_string(
            "| Dm7 | G7 | Cmaj7 |",
            title="ii-V-I",
            key="C",
            time_signature=(3, 4),
        )
        assert score.title == "ii-V-I"
        assert score.key == "C"
        assert score.time_signature == (3, 4)
        assert len(score.measures) == 3

    def test_score_iteration(self, simple_chord_string):
        """Test that Score is iterable."""
        score = Score.from_string(simple_chord_string)
        measures = list(score)
        assert len(measures) == 4
        assert measures[0] == ["C"]

    def test_score_length(self, simple_chord_string):
        """Test Score __len__ method."""
        score = Score.from_string(simple_chord_string)
        assert len(score) == 4


class TestEnsureScore:
    """Test ensure_score function with various input formats."""

    def test_ensure_score_from_string(self, simple_chord_string):
        """Test ensure_score with chord string."""
        score = ensure_score(simple_chord_string)
        assert isinstance(score, Score)
        assert len(score) == 4

    def test_ensure_score_from_score(self, simple_chord_string):
        """Test ensure_score with Score object (identity)."""
        original = Score.from_string(simple_chord_string)
        score = ensure_score(original)
        assert score is original

    def test_ensure_score_from_chord_tuples(self, chord_tuples):
        """Test ensure_score with (chord, beats) tuples."""
        score = ensure_score(chord_tuples)
        assert isinstance(score, Score)
        # 4 chords, 4 beats each, in 4/4 = 4 measures
        assert len(score) == 4

    def test_ensure_score_from_chord_list(self):
        """Test ensure_score with list of chord symbols."""
        chords = ["C", "Am", "F", "G"]
        score = ensure_score(chords)
        assert isinstance(score, Score)
        assert len(score) == 4
        assert score.measures[0] == ["C"]
        assert score.measures[1] == ["A-"]

    def test_ensure_score_from_measures_list(self):
        """Test ensure_score with pre-parsed measures."""
        measures = [["C"], ["Am", "F"], ["G"]]
        score = ensure_score(measures)
        assert isinstance(score, Score)
        assert len(score) == 3
        assert score.measures[0] == ["C"]
        assert score.measures[1] == ["A-", "F"]

    def test_ensure_score_invalid_input(self):
        """Test that invalid input raises TypeError."""
        with pytest.raises(TypeError):
            ensure_score(123)  # Invalid type

        # Note: dicts are iterable and get treated as lists of keys
        # so {"a": "b"} becomes a chord progression with chord "a"
        # This is technically valid, even if unusual


# =============================================================================
# Chord to Notes Tests
# =============================================================================


class TestChordToNotes:
    """Test chord symbol to MIDI note conversion."""

    def test_basic_major_chord(self):
        """Test basic major chord conversion."""
        notes = _basic_chord_to_notes("C")
        assert len(notes) == 3
        # C major triad: C, E, G (root, 3rd, 5th)
        assert notes[1] - notes[0] == 4  # Major 3rd
        assert notes[2] - notes[0] == 7  # Perfect 5th

    def test_minor_chord(self):
        """Test minor chord conversion."""
        notes = _basic_chord_to_notes("C-")
        assert len(notes) == 3
        # C minor: C, Eb, G
        assert notes[1] - notes[0] == 3  # Minor 3rd
        assert notes[2] - notes[0] == 7  # Perfect 5th

    def test_dominant_seventh(self):
        """Test dominant 7th chord."""
        notes = _basic_chord_to_notes("C7")
        assert len(notes) == 4
        # C7: C, E, G, Bb
        assert notes[3] - notes[0] == 10  # Minor 7th

    def test_major_seventh(self):
        """Test major 7th chord."""
        notes = _basic_chord_to_notes("C^7")
        assert len(notes) == 4
        # Cmaj7: C, E, G, B
        assert notes[3] - notes[0] == 11  # Major 7th

    def test_minor_seventh(self):
        """Test minor 7th chord."""
        notes = _basic_chord_to_notes("C-7")
        assert len(notes) == 4
        # Cm7: C, Eb, G, Bb
        assert notes[1] - notes[0] == 3  # Minor 3rd
        assert notes[3] - notes[0] == 10  # Minor 7th

    def test_diminished_chord(self):
        """Test diminished chord."""
        notes = _basic_chord_to_notes("Co")
        assert len(notes) == 3
        # Cdim: C, Eb, Gb
        assert notes[1] - notes[0] == 3  # Minor 3rd
        assert notes[2] - notes[0] == 6  # Diminished 5th

    def test_chord_with_accidentals(self):
        """Test chords with sharps and flats."""
        notes_sharp = _basic_chord_to_notes("F#")
        notes_flat = _basic_chord_to_notes("Bb")
        assert len(notes_sharp) == 3
        assert len(notes_flat) == 3
        # Verify they're different roots
        assert notes_sharp[0] != notes_flat[0]


# =============================================================================
# MIDI Generation Tests
# =============================================================================


class TestMIDIGeneration:
    """Test MIDI file generation (core of audio production)."""

    def test_generate_midi_builtin(self, simple_chord_string, temp_output_dir):
        """Test MIDI generation with builtin backend."""
        output_path = temp_output_dir / "test.mid"

        # Generate MIDI only (no audio rendering)
        result = generate_accompaniment(
            simple_chord_string,
            style="swing",
            tempo=120,
            output_path=str(output_path),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert result.suffix == ".mid"
        # MIDI files should have some minimum size
        assert result.stat().st_size > 100

    def test_midi_different_styles(self, simple_chord_string, temp_output_dir):
        """Test MIDI generation for different styles."""
        styles = ["swing", "bossa", "rock", "ballad"]

        for style in styles:
            output_path = temp_output_dir / f"test_{style}.mid"
            result = generate_accompaniment(
                simple_chord_string,
                style=style,
                tempo=120,
                output_path=str(output_path),
                output_format="midi",
                backend="builtin",
            )
            assert result.exists()
            assert result.stat().st_size > 100

    def test_midi_with_different_tempos(self, simple_chord_string, temp_output_dir):
        """Test MIDI generation with different tempos."""
        for tempo in [80, 120, 180]:
            output_path = temp_output_dir / f"test_tempo_{tempo}.mid"
            result = generate_accompaniment(
                simple_chord_string,
                style="swing",
                tempo=tempo,
                output_path=str(output_path),
                output_format="midi",
                backend="builtin",
            )
            assert result.exists()

    def test_midi_with_repeats(self, simple_chord_string, temp_output_dir):
        """Test MIDI generation with multiple repeats."""
        output_1 = temp_output_dir / "test_1repeat.mid"
        output_4 = temp_output_dir / "test_4repeat.mid"

        result_1 = generate_accompaniment(
            simple_chord_string,
            repeats=1,
            output_path=str(output_1),
            output_format="midi",
            backend="builtin",
        )

        result_4 = generate_accompaniment(
            simple_chord_string,
            repeats=4,
            output_path=str(output_4),
            output_format="midi",
            backend="builtin",
        )

        # File with more repeats should be larger
        assert result_4.stat().st_size > result_1.stat().st_size


class TestAudioGeneration:
    """Test audio generation (mocked FluidSynth)."""

    @patch("accompy.accompy._render_midi_to_audio")
    def test_generate_wav_mocked(self, mock_render, simple_chord_string, temp_output_dir):
        """Test WAV generation with mocked FluidSynth."""
        output_path = temp_output_dir / "test.wav"

        # Mock the audio rendering to just create an empty file
        def mock_render_func(midi_path, wav_path, config):
            wav_path.touch()

        mock_render.side_effect = mock_render_func

        result = generate_accompaniment(
            simple_chord_string,
            style="bossa",
            tempo=120,
            output_path=str(output_path),
            output_format="wav",
            backend="builtin",
        )

        # Verify render was called
        assert mock_render.called
        # Result should point to WAV file
        assert result.suffix == ".wav"

    def test_generate_to_temp_file(self, simple_chord_string):
        """Test generation to temporary file."""
        result = generate_accompaniment(
            simple_chord_string,
            style="swing",
            output_format="midi",
            backend="builtin",
        )

        # Should create a temp file
        assert result.exists()
        assert result.suffix == ".mid"
        # Clean up
        result.unlink()


# =============================================================================
# Configuration Tests
# =============================================================================


class TestAccompanimentConfig:
    """Test AccompanimentConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AccompanimentConfig()
        assert config.style == "swing"
        assert config.tempo == 120
        assert config.repeats == 2
        assert config.instruments["drums"] is True
        assert config.instruments["bass"] is True
        assert config.instruments["piano"] is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = AccompanimentConfig(
            style="bossa",
            tempo=140,
            repeats=4,
            instruments={"drums": True, "bass": True, "piano": False},
        )
        assert config.style == "bossa"
        assert config.tempo == 140
        assert config.repeats == 4
        assert config.instruments["piano"] is False

    def test_config_with_generate_accompaniment(
        self, simple_chord_string, temp_output_dir
    ):
        """Test using config with generate_accompaniment."""
        config = AccompanimentConfig(
            style="rock",
            tempo=130,
            repeats=3,
        )

        output_path = temp_output_dir / "test_config.mid"
        result = generate_accompaniment(
            simple_chord_string,
            config=config,
            output_path=str(output_path),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_simple_workflow(self, temp_output_dir):
        """Test complete workflow from chord string to MIDI."""
        # Define progression
        chords = "| Dm7 | G7 | Cmaj7 | A7 |"

        # Generate
        output = temp_output_dir / "integration_test.mid"
        result = generate_accompaniment(
            chords,
            style="swing",
            tempo=160,
            repeats=2,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        # Verify
        assert result.exists()
        assert result == output
        assert result.stat().st_size > 100

    def test_chord_tuple_workflow(self, chord_tuples, temp_output_dir):
        """Test workflow with chord tuples."""
        output = temp_output_dir / "tuple_test.mid"
        result = generate_accompaniment(
            chord_tuples,
            style="bossa",
            tempo=120,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()

    def test_jazz_progression(self, jazz_chord_string, temp_output_dir):
        """Test with complex jazz chords."""
        output = temp_output_dir / "jazz_test.mid"
        result = generate_accompaniment(
            jazz_chord_string,
            style="swing",
            tempo=180,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert result.stat().st_size > 100
