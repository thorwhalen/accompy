"""Tests for accompy patterns module."""

import pytest

from accompy.patterns import (
    DrumPattern,
    BassPattern,
    CompingPattern,
    DrumHit,
    NoteEvent,
    get_patterns,
    KICK,
    SNARE,
    CLOSED_HIHAT,
    SWING_DRUMS_BASIC,
    SWING_BASS_WALKING,
    BOSSA_DRUMS,
    BOSSA_BASS,
    ROCK_DRUMS_BASIC,
    WALTZ_DRUMS,
)


# =============================================================================
# Pattern Data Structure Tests
# =============================================================================


class TestDrumHit:
    """Test DrumHit dataclass."""

    def test_drum_hit_creation(self):
        """Test creating a DrumHit."""
        hit = DrumHit(beat=0, drum=KICK, velocity=100)
        assert hit.beat == 0
        assert hit.drum == KICK
        assert hit.velocity == 100

    def test_drum_hit_immutable(self):
        """Test that DrumHit is frozen/immutable."""
        hit = DrumHit(beat=0, drum=KICK, velocity=100)
        with pytest.raises(AttributeError):
            hit.beat = 1  # Should raise because frozen=True


class TestNoteEvent:
    """Test NoteEvent dataclass."""

    def test_note_event_creation(self):
        """Test creating a NoteEvent."""
        note = NoteEvent(beat=0, pitch_offset=0, duration=1.0, velocity=90)
        assert note.beat == 0
        assert note.pitch_offset == 0
        assert note.duration == 1.0
        assert note.velocity == 90

    def test_note_event_immutable(self):
        """Test that NoteEvent is frozen/immutable."""
        note = NoteEvent(beat=0, pitch_offset=0, duration=1.0, velocity=90)
        with pytest.raises(AttributeError):
            note.beat = 1


# =============================================================================
# Pattern Class Tests
# =============================================================================


class TestDrumPattern:
    """Test DrumPattern class."""

    def test_drum_pattern_creation(self):
        """Test creating a DrumPattern."""
        pattern = DrumPattern(
            name="test",
            beats_per_bar=4,
            hits=[
                DrumHit(0, KICK, 100),
                DrumHit(1, SNARE, 90),
            ],
        )
        assert pattern.name == "test"
        assert pattern.beats_per_bar == 4
        assert len(pattern.hits) == 2

    def test_drum_pattern_at_tempo(self):
        """Test calculating pattern duration at different tempos."""
        pattern = DrumPattern(
            name="test",
            beats_per_bar=4,
            hits=[],
        )
        # At 120 BPM: 60/120 = 0.5 seconds per beat
        # 4 beats = 2 seconds
        assert pattern.at_tempo(120) == pytest.approx(2.0)
        # At 60 BPM: 60/60 = 1 second per beat
        # 4 beats = 4 seconds
        assert pattern.at_tempo(60) == pytest.approx(4.0)


class TestBassPattern:
    """Test BassPattern class."""

    def test_bass_pattern_creation(self):
        """Test creating a BassPattern."""
        pattern = BassPattern(
            name="walking",
            notes=[
                NoteEvent(0, 0, 0.9, 100),
                NoteEvent(1, 4, 0.9, 90),
            ],
        )
        assert pattern.name == "walking"
        assert len(pattern.notes) == 2


class TestCompingPattern:
    """Test CompingPattern class."""

    def test_comping_pattern_creation(self):
        """Test creating a CompingPattern."""
        pattern = CompingPattern(
            name="swing_comp",
            hits=[
                (1.5, 0.4, 75),
                (3.5, 0.4, 80),
            ],
        )
        assert pattern.name == "swing_comp"
        assert len(pattern.hits) == 2


# =============================================================================
# Built-in Pattern Tests
# =============================================================================


class TestBuiltInPatterns:
    """Test that built-in patterns are valid."""

    def test_swing_drum_pattern(self):
        """Test swing drum pattern."""
        assert SWING_DRUMS_BASIC.name == "swing_basic"
        assert SWING_DRUMS_BASIC.beats_per_bar == 4
        assert len(SWING_DRUMS_BASIC.hits) > 0
        # Verify all hits are within the bar
        for hit in SWING_DRUMS_BASIC.hits:
            assert 0 <= hit.beat < 4

    def test_swing_bass_pattern(self):
        """Test swing bass pattern."""
        assert SWING_BASS_WALKING.name == "walking"
        assert len(SWING_BASS_WALKING.notes) == 4
        # Walking bass should have a note on each beat
        beat_positions = [note.beat for note in SWING_BASS_WALKING.notes]
        assert beat_positions == [0, 1, 2, 3]

    def test_bossa_drum_pattern(self):
        """Test bossa nova drum pattern."""
        assert BOSSA_DRUMS.name == "bossa"
        assert BOSSA_DRUMS.beats_per_bar == 4
        # Bossa should have syncopation
        assert len(BOSSA_DRUMS.hits) > 0

    def test_bossa_bass_pattern(self):
        """Test bossa bass pattern."""
        assert BOSSA_BASS.name == "bossa"
        # Bossa bass typically has syncopated rhythm
        assert len(BOSSA_BASS.notes) >= 2

    def test_rock_drum_pattern(self):
        """Test rock drum pattern."""
        assert ROCK_DRUMS_BASIC.name == "rock_basic"
        assert ROCK_DRUMS_BASIC.beats_per_bar == 4
        # Rock should have kick and snare
        drums_used = {hit.drum for hit in ROCK_DRUMS_BASIC.hits}
        assert KICK in drums_used
        assert SNARE in drums_used

    def test_waltz_drum_pattern(self):
        """Test waltz pattern in 3/4."""
        assert WALTZ_DRUMS.name == "waltz"
        assert WALTZ_DRUMS.beats_per_bar == 3
        # All hits should be within 3 beats
        for hit in WALTZ_DRUMS.hits:
            assert 0 <= hit.beat < 3


# =============================================================================
# Pattern Retrieval Tests
# =============================================================================


class TestGetPatterns:
    """Test get_patterns function."""

    def test_get_swing_patterns(self):
        """Test retrieving swing patterns."""
        patterns = get_patterns("swing")
        assert "drums" in patterns
        assert "bass" in patterns
        assert "comp" in patterns
        assert len(patterns["drums"]) > 0
        assert len(patterns["bass"]) > 0

    def test_get_bossa_patterns(self):
        """Test retrieving bossa patterns."""
        patterns = get_patterns("bossa")
        assert len(patterns["drums"]) > 0
        assert len(patterns["bass"]) > 0

    def test_get_rock_patterns(self):
        """Test retrieving rock patterns."""
        patterns = get_patterns("rock")
        assert len(patterns["drums"]) > 0
        assert len(patterns["bass"]) > 0

    def test_get_all_styles(self):
        """Test that patterns exist for all common styles."""
        styles = ["swing", "bossa", "rock", "ballad", "funk", "latin", "waltz", "blues"]
        for style in styles:
            patterns = get_patterns(style)
            assert "drums" in patterns
            assert "bass" in patterns
            assert "comp" in patterns
            # Each style should have at least one drum and bass pattern
            assert len(patterns["drums"]) > 0
            assert len(patterns["bass"]) > 0

    def test_get_unknown_style_defaults_to_swing(self):
        """Test that unknown style returns swing patterns."""
        patterns = get_patterns("unknown_style")
        swing_patterns = get_patterns("swing")
        # Should get same patterns as swing
        assert patterns["drums"] == swing_patterns["drums"]
        assert patterns["bass"] == swing_patterns["bass"]


# =============================================================================
# Pattern Validation Tests
# =============================================================================


class TestPatternValidation:
    """Test that patterns have valid data."""

    def test_drum_velocities_in_range(self):
        """Test that all drum hit velocities are valid MIDI values."""
        patterns = get_patterns("swing")
        for pattern in patterns["drums"]:
            for hit in pattern.hits:
                assert 0 <= hit.velocity <= 127

    def test_bass_velocities_in_range(self):
        """Test that all bass note velocities are valid MIDI values."""
        patterns = get_patterns("swing")
        for pattern in patterns["bass"]:
            for note in pattern.notes:
                assert 0 <= note.velocity <= 127

    def test_beat_positions_non_negative(self):
        """Test that all beat positions are non-negative."""
        for style in ["swing", "bossa", "rock"]:
            patterns = get_patterns(style)
            for pattern in patterns["drums"]:
                for hit in pattern.hits:
                    assert hit.beat >= 0
            for pattern in patterns["bass"]:
                for note in pattern.notes:
                    assert note.beat >= 0

    def test_note_durations_positive(self):
        """Test that all note durations are positive."""
        for style in ["swing", "bossa", "rock"]:
            patterns = get_patterns(style)
            for pattern in patterns["bass"]:
                for note in pattern.notes:
                    assert note.duration > 0


# =============================================================================
# MIDI Drum Note Tests
# =============================================================================


class TestMIDIDrumNotes:
    """Test MIDI drum note constants."""

    def test_drum_notes_are_unique(self):
        """Test that drum notes have unique values."""
        notes = [KICK, SNARE, CLOSED_HIHAT]
        assert len(notes) == len(set(notes))

    def test_drum_notes_in_valid_range(self):
        """Test that drum notes are valid MIDI note numbers."""
        drum_notes = [KICK, SNARE, CLOSED_HIHAT]
        for note in drum_notes:
            assert 0 <= note <= 127


# =============================================================================
# Pattern Consistency Tests
# =============================================================================


class TestPatternConsistency:
    """Test consistency across patterns."""

    def test_same_style_patterns_same_time_signature(self):
        """Test that patterns for same style have consistent time signatures."""
        patterns = get_patterns("swing")
        # All swing drum patterns should be in 4/4
        for pattern in patterns["drums"]:
            assert pattern.beats_per_bar == 4

        # Waltz should be 3/4
        waltz = get_patterns("waltz")
        for pattern in waltz["drums"]:
            assert pattern.beats_per_bar == 3

    def test_patterns_have_content(self):
        """Test that all patterns have actual hits/notes."""
        for style in ["swing", "bossa", "rock", "ballad"]:
            patterns = get_patterns(style)
            # All drum patterns should have hits
            for pattern in patterns["drums"]:
                assert len(pattern.hits) > 0
            # All bass patterns should have notes
            for pattern in patterns["bass"]:
                assert len(pattern.notes) > 0
