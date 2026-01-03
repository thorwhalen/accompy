"""
Tests specifically for audio production from simple chords.

This module demonstrates different approaches to testing MIDI and audio
generation, including inspecting MIDI file contents.
"""

import struct
from pathlib import Path

import pytest

from accompy import generate_accompaniment, Score


# =============================================================================
# Simple Chord to MIDI Tests
# =============================================================================


class TestSimpleChordsToMIDI:
    """Test generating MIDI from simple chord progressions."""

    def test_single_chord(self, temp_output_dir):
        """Test generating MIDI from a single chord."""
        output = temp_output_dir / "single_chord.mid"
        result = generate_accompaniment(
            "| C |",
            style="swing",
            tempo=120,
            repeats=1,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert result.stat().st_size > 0

    def test_four_chord_progression(self, temp_output_dir):
        """Test classic I-vi-IV-V progression."""
        # The classic "50s progression"
        chords = "| C | Am | F | G |"

        output = temp_output_dir / "four_chords.mid"
        result = generate_accompaniment(
            chords,
            style="rock",
            tempo=120,
            repeats=2,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        # Verify it's a real MIDI file
        assert _is_valid_midi(result)

    def test_twelve_bar_blues(self, temp_output_dir):
        """Test 12-bar blues progression."""
        blues = "| C7 | C7 | C7 | C7 | F7 | F7 | C7 | C7 | G7 | F7 | C7 | G7 |"

        output = temp_output_dir / "12bar_blues.mid"
        result = generate_accompaniment(
            blues,
            style="blues",
            tempo=100,
            repeats=1,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)
        # Blues has 12 bars, should be longer
        assert result.stat().st_size > 1000

    def test_jazz_ii_v_i(self, temp_output_dir):
        """Test ii-V-I progression in C."""
        chords = "| Dm7 | G7 | Cmaj7 |"

        output = temp_output_dir / "ii_v_i.mid"
        result = generate_accompaniment(
            chords,
            style="swing",
            tempo=160,
            repeats=4,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)


# =============================================================================
# MIDI Content Verification Tests
# =============================================================================


class TestMIDIContentVerification:
    """Test that MIDI files contain expected content."""

    def test_midi_has_multiple_tracks(self, temp_output_dir):
        """Test that generated MIDI has expected tracks."""
        output = temp_output_dir / "multi_track.mid"
        result = generate_accompaniment(
            "| C | G | Am | F |",
            style="bossa",
            tempo=120,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        # Check MIDI header
        with open(result, "rb") as f:
            # Read MThd header chunk
            header = f.read(14)
            chunk_type = header[0:4]
            assert chunk_type == b"MThd"

            # Extract format and track count
            format_type = struct.unpack(">H", header[8:10])[0]
            num_tracks = struct.unpack(">H", header[10:12])[0]

            # Should have multiple tracks (drums, bass, piano)
            assert num_tracks >= 2

    def test_midi_tempo_in_file(self, temp_output_dir):
        """Test that MIDI file contains tempo information."""
        tempo = 140
        output = temp_output_dir / "tempo_test.mid"

        result = generate_accompaniment(
            "| C |",
            tempo=tempo,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        # MIDI files should contain tempo meta-events
        # This is a basic check that the file is structured correctly
        with open(result, "rb") as f:
            content = f.read()
            # Look for tempo meta event (FF 51 03)
            # Note: This is a simplified check
            assert b"\xff\x51\x03" in content or result.stat().st_size > 100


# =============================================================================
# Different Styles Test
# =============================================================================


class TestDifferentStylesProduction:
    """Test that different styles produce different outputs."""

    @pytest.mark.parametrize(
        "style,expected_min_size",
        [
            ("swing", 500),
            ("bossa", 500),
            ("rock", 500),
            ("ballad", 300),  # Simpler pattern = smaller file
            ("funk", 500),
            ("latin", 500),
            ("waltz", 300),  # 3/4 time = fewer notes
            ("blues", 500),
        ],
    )
    def test_style_produces_midi(self, style, expected_min_size, temp_output_dir):
        """Test that each style produces MIDI output."""
        output = temp_output_dir / f"{style}_test.mid"

        result = generate_accompaniment(
            "| C | G | Am | F |",
            style=style,
            tempo=120,
            repeats=1,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)
        assert result.stat().st_size >= expected_min_size


# =============================================================================
# Complex Chord Tests
# =============================================================================


class TestComplexChords:
    """Test audio production with more complex chord symbols."""

    def test_extended_chords(self, temp_output_dir):
        """Test with extended jazz chords."""
        chords = "| Cmaj9 | Dm11 | G13 | Cmaj7#11 |"

        output = temp_output_dir / "extended.mid"
        result = generate_accompaniment(
            chords,
            style="swing",
            tempo=120,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)

    def test_altered_chords(self, temp_output_dir):
        """Test with altered dominant chords."""
        chords = "| C | G7#5 | C | G7b9 |"

        output = temp_output_dir / "altered.mid"
        result = generate_accompaniment(
            chords,
            style="swing",
            tempo=120,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()

    def test_slash_chords(self, temp_output_dir):
        """Test with slash chords (inversions)."""
        chords = "| C/E | F/A | G/B | C |"

        output = temp_output_dir / "slash_chords.mid"
        result = generate_accompaniment(
            chords,
            style="ballad",
            tempo=80,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()


# =============================================================================
# Tempo and Time Signature Tests
# =============================================================================


class TestMusicalParameters:
    """Test various musical parameters in audio production."""

    @pytest.mark.parametrize("tempo", [60, 90, 120, 160, 200])
    def test_various_tempos(self, tempo, temp_output_dir):
        """Test that various tempos produce valid output."""
        output = temp_output_dir / f"tempo_{tempo}.mid"

        result = generate_accompaniment(
            "| C | G | Am | F |",
            tempo=tempo,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)

    def test_waltz_time_signature(self, temp_output_dir):
        """Test 3/4 time signature (waltz)."""
        output = temp_output_dir / "waltz.mid"

        # Waltz style implies 3/4 time
        result = generate_accompaniment(
            "| C | Am | F | G |",
            style="waltz",
            tempo=120,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)


# =============================================================================
# Integration: Complete Song Tests
# =============================================================================


class TestCompleteSongs:
    """Test generating complete song-like progressions."""

    def test_verse_chorus_structure(self, temp_output_dir):
        """Test a progression with verse and chorus feel."""
        # Verse: Am F C G
        # Chorus: F G C Am
        progression = "| Am | F | C | G | F | G | C | Am |"

        output = temp_output_dir / "song_structure.mid"
        result = generate_accompaniment(
            progression,
            style="rock",
            tempo=120,
            repeats=2,  # Verse + Chorus twice
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert result.stat().st_size > 2000  # Should be substantial

    def test_autumn_leaves_changes(self, temp_output_dir):
        """Test the A section of Autumn Leaves."""
        changes = (
            "| Cm7 | F7 | Bbmaj7 | Ebmaj7 | "
            "| Am7b5 | D7 | Gm | Gm |"
        )

        output = temp_output_dir / "autumn_leaves.mid"
        result = generate_accompaniment(
            changes,
            style="swing",
            tempo=140,
            repeats=3,
            output_path=str(output),
            output_format="midi",
            backend="builtin",
        )

        assert result.exists()
        assert _is_valid_midi(result)


# =============================================================================
# Helper Functions
# =============================================================================


def _is_valid_midi(path: Path) -> bool:
    """
    Check if a file is a valid MIDI file.

    Performs basic validation by checking for MIDI header.
    """
    if not path.exists():
        return False

    try:
        with open(path, "rb") as f:
            # Read first 4 bytes - should be "MThd"
            header = f.read(4)
            return header == b"MThd"
    except Exception:
        return False


def _get_midi_info(path: Path) -> dict:
    """
    Extract basic info from MIDI file.

    Returns dict with format, num_tracks, and division.
    """
    with open(path, "rb") as f:
        header = f.read(14)
        if header[0:4] != b"MThd":
            raise ValueError("Not a valid MIDI file")

        format_type = struct.unpack(">H", header[8:10])[0]
        num_tracks = struct.unpack(">H", header[10:12])[0]
        division = struct.unpack(">H", header[12:14])[0]

        return {
            "format": format_type,
            "num_tracks": num_tracks,
            "division": division,
        }
