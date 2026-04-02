"""Tests for accompy.rhythmic_skeletons."""

import pytest

from accompy.rhythmic_skeletons import (
    RHYTHMIC_SKELETONS,
    resolve_skeleton,
    apply_skeleton,
    register_skeleton,
    list_skeletons,
    _group_into_measures,
)
from accompy.converters import ChordSequence


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------


class TestSkeletonData:
    """Verify the built-in skeleton dictionary is well-formed."""

    def test_all_have_required_keys(self):
        required = {"pattern", "name", "beats_per_measure", "styles"}
        for key, entry in RHYTHMIC_SKELETONS.items():
            missing = required - entry.keys()
            assert not missing, f"{key!r} is missing keys: {missing}"

    def test_patterns_sum_to_beats_per_measure(self):
        for key, entry in RHYTHMIC_SKELETONS.items():
            total = sum(entry["pattern"])
            assert abs(total - entry["beats_per_measure"]) < 1e-9, (
                f"{key!r}: sum({entry['pattern']}) = {total}, "
                f"expected {entry['beats_per_measure']}"
            )

    def test_no_zero_or_negative_durations(self):
        for key, entry in RHYTHMIC_SKELETONS.items():
            for dur in entry["pattern"]:
                assert dur > 0, f"{key!r} has non-positive duration: {dur}"

    def test_patterns_are_tuples(self):
        for key, entry in RHYTHMIC_SKELETONS.items():
            assert isinstance(entry["pattern"], tuple), (
                f"{key!r} pattern is {type(entry['pattern']).__name__}, expected tuple"
            )

    def test_styles_are_lists_of_strings(self):
        for key, entry in RHYTHMIC_SKELETONS.items():
            assert isinstance(entry["styles"], list), f"{key!r} styles not a list"
            for s in entry["styles"]:
                assert isinstance(s, str), f"{key!r} has non-string style: {s!r}"

    def test_has_expected_entries(self):
        expected = [
            "whole_note", "half_notes", "quarter_notes", "four_on_the_floor",
            "tresillo", "charleston", "waltz_quarters",
        ]
        for key in expected:
            assert key in RHYTHMIC_SKELETONS, f"Missing expected skeleton: {key!r}"

    def test_quarter_notes_and_four_on_the_floor_same_pattern(self):
        assert (
            RHYTHMIC_SKELETONS["quarter_notes"]["pattern"]
            == RHYTHMIC_SKELETONS["four_on_the_floor"]["pattern"]
        )


# ---------------------------------------------------------------------------
# resolve_skeleton
# ---------------------------------------------------------------------------


class TestResolveSkeleton:
    def test_resolve_by_key(self):
        assert resolve_skeleton("whole_note") == (4,)
        assert resolve_skeleton("tresillo") == (1.5, 1.5, 1)

    def test_resolve_by_name_case_insensitive(self):
        assert resolve_skeleton("Tresillo") == (1.5, 1.5, 1)
        assert resolve_skeleton("tresillo") == (1.5, 1.5, 1)
        assert resolve_skeleton("WHOLE NOTE") == (4,)

    def test_resolve_by_name_with_special_chars(self):
        assert resolve_skeleton("Dotted half + quarter") == (3, 1)
        assert resolve_skeleton("dotted half + quarter") == (3, 1)

    def test_resolve_by_style(self):
        pattern = resolve_skeleton("reggae")
        assert isinstance(pattern, tuple)
        assert all(d > 0 for d in pattern)

    def test_resolve_tuple_passthrough(self):
        assert resolve_skeleton((2, 2)) == (2, 2)
        assert resolve_skeleton((1.5, 1.5, 1)) == (1.5, 1.5, 1)

    def test_resolve_list_passthrough(self):
        assert resolve_skeleton([1, 1, 1, 1]) == (1, 1, 1, 1)

    def test_resolve_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown skeleton"):
            resolve_skeleton("nonexistent_skeleton_xyz")

    def test_resolve_wrong_type_raises_type_error(self):
        with pytest.raises(TypeError):
            resolve_skeleton(42)


# ---------------------------------------------------------------------------
# apply_skeleton
# ---------------------------------------------------------------------------


class TestApplySkeleton:
    """Test the core skeleton-to-chord-sequence expansion."""

    def test_whole_note_is_identity(self):
        """Whole-note skeleton should not change a one-chord-per-measure sequence."""
        cs = ChordSequence([("C", 4.0), ("Am", 4.0)])
        result = apply_skeleton(cs, "whole_note")
        assert list(result) == [("C", 4.0), ("Am", 4.0)]

    def test_simple_single_chord_per_measure(self):
        """Tresillo on single-chord measures should expand each measure."""
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
        result = apply_skeleton(cs, "tresillo")
        expected = [
            ("Dm7", 1.5), ("Dm7", 1.5), ("Dm7", 1.0),
            ("G7", 1.5), ("G7", 1.5), ("G7", 1.0),
        ]
        assert list(result) == expected

    def test_two_chords_per_measure_with_boundary_split(self):
        """Tresillo across a chord boundary should split correctly."""
        cs = ChordSequence([("Dm7", 2.0), ("G7", 2.0)])
        result = apply_skeleton(cs, "tresillo")
        # Skeleton (1.5, 1.5, 1) on measure with Dm7@[0,2), G7@[2,4):
        # Strike 0: beat 0, dur 1.5 → Dm7(1.5)
        # Strike 1: beat 1.5, dur 1.5 → Dm7(0.5), G7(1.0)
        # Strike 2: beat 3, dur 1.0 → G7(1.0)
        expected = [("Dm7", 1.5), ("Dm7", 0.5), ("G7", 1.0), ("G7", 1.0)]
        assert list(result) == expected

    def test_half_notes_on_four_beat_measure(self):
        cs = ChordSequence([("C", 4.0)])
        result = apply_skeleton(cs, "half_notes")
        assert list(result) == [("C", 2.0), ("C", 2.0)]

    def test_quarter_notes_expansion(self):
        cs = ChordSequence([("Am", 4.0)])
        result = apply_skeleton(cs, "quarter_notes")
        assert list(result) == [("Am", 1.0)] * 4

    def test_waltz_skeleton_on_3_beat_measure(self):
        cs = ChordSequence([("C", 3.0), ("G", 3.0)], time_signature=(3, 4))
        result = apply_skeleton(cs, "waltz_quarters")
        expected = [("C", 1.0)] * 3 + [("G", 1.0)] * 3
        assert list(result) == expected

    def test_tuple_skeleton(self):
        cs = ChordSequence([("C", 4.0)])
        result = apply_skeleton(cs, (3, 1))
        assert list(result) == [("C", 3.0), ("C", 1.0)]

    def test_multi_measure_progression(self):
        cs = ChordSequence([("C", 4.0), ("Am", 4.0), ("F", 4.0), ("G", 4.0)])
        result = apply_skeleton(cs, "half_notes")
        expected = [
            ("C", 2.0), ("C", 2.0),
            ("Am", 2.0), ("Am", 2.0),
            ("F", 2.0), ("F", 2.0),
            ("G", 2.0), ("G", 2.0),
        ]
        assert list(result) == expected

    def test_preserves_metadata(self):
        cs = ChordSequence(
            [("C", 4.0)],
            title="Test",
            key="C",
            tempo=140,
            time_signature=(4, 4),
        )
        result = apply_skeleton(cs, "tresillo")
        assert result.title == "Test"
        assert result.key == "C"
        assert result.tempo == 140
        assert result.time_signature == (4, 4)

    def test_total_beats_preserved(self):
        """Expanding a skeleton should not change the total beat count."""
        cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
        result = apply_skeleton(cs, "charleston")
        assert abs(result.total_beats - cs.total_beats) < 1e-9

    def test_chord_spanning_two_measures(self):
        """An 8-beat chord should be split across two 4-beat measures."""
        cs = ChordSequence([("C", 8.0)])
        result = apply_skeleton(cs, "half_notes")
        # 8 beats → 2 measures of 4 beats each
        # Each measure: (C, 2.0), (C, 2.0)
        expected = [("C", 2.0), ("C", 2.0), ("C", 2.0), ("C", 2.0)]
        assert list(result) == expected


# ---------------------------------------------------------------------------
# _group_into_measures
# ---------------------------------------------------------------------------


class TestGroupIntoMeasures:
    def test_simple_grouping(self):
        chords = [("C", 4.0), ("Am", 4.0)]
        measures = _group_into_measures(chords, 4.0)
        assert len(measures) == 2
        assert measures[0] == [("C", 4.0)]
        assert measures[1] == [("Am", 4.0)]

    def test_two_chords_per_measure(self):
        chords = [("C", 2.0), ("G", 2.0), ("Am", 2.0), ("F", 2.0)]
        measures = _group_into_measures(chords, 4.0)
        assert len(measures) == 2
        assert measures[0] == [("C", 2.0), ("G", 2.0)]
        assert measures[1] == [("Am", 2.0), ("F", 2.0)]

    def test_chord_spanning_measure_boundary(self):
        chords = [("C", 6.0), ("G", 2.0)]
        measures = _group_into_measures(chords, 4.0)
        assert len(measures) == 2
        assert measures[0] == [("C", 4.0)]
        assert measures[1] == [("C", 2.0), ("G", 2.0)]


# ---------------------------------------------------------------------------
# register_skeleton
# ---------------------------------------------------------------------------


class TestRegisterSkeleton:
    def test_register_and_resolve(self):
        register_skeleton("test_custom", (1.5, 0.5, 2), name="Test Custom")
        assert resolve_skeleton("test_custom") == (1.5, 0.5, 2)
        assert resolve_skeleton("Test Custom") == (1.5, 0.5, 2)
        # Cleanup
        del RHYTHMIC_SKELETONS["test_custom"]

    def test_register_with_styles(self):
        register_skeleton(
            "test_styled", (2, 2), name="Test Styled", styles=["test_style_xyz"]
        )
        assert resolve_skeleton("test_style_xyz") == (2, 2)
        # Cleanup
        del RHYTHMIC_SKELETONS["test_styled"]

    def test_register_defaults_beats_per_measure(self):
        register_skeleton("test_auto_bpm", (1.5, 1.5, 1))
        assert RHYTHMIC_SKELETONS["test_auto_bpm"]["beats_per_measure"] == 4.0
        # Cleanup
        del RHYTHMIC_SKELETONS["test_auto_bpm"]


# ---------------------------------------------------------------------------
# list_skeletons
# ---------------------------------------------------------------------------


class TestListSkeletons:
    def test_list_all(self):
        keys = list_skeletons()
        assert "tresillo" in keys
        assert "whole_note" in keys
        assert len(keys) >= 20

    def test_filter_by_beats_per_measure(self):
        waltz_keys = list_skeletons(beats_per_measure=3)
        assert all(
            RHYTHMIC_SKELETONS[k]["beats_per_measure"] == 3 for k in waltz_keys
        )
        assert "waltz_quarters" in waltz_keys
        assert "tresillo" not in waltz_keys

    def test_filter_by_style(self):
        reggae_keys = list_skeletons(style="reggae")
        assert len(reggae_keys) >= 1
        for k in reggae_keys:
            assert "reggae" in RHYTHMIC_SKELETONS[k]["styles"]


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    def test_rhythm_to_midi_basic(self):
        from accompy.pipeline import rhythm_to_midi

        md = rhythm_to_midi("| C | Am | F | G |", skeleton="tresillo", tempo=120)
        midi_bytes = md.to_bytes()
        assert midi_bytes[:4] == b"MThd"

    def test_rhythm_to_midi_default_skeleton(self):
        from accompy.pipeline import rhythm_to_midi

        md = rhythm_to_midi("| C | Am |", tempo=120)
        assert md.to_bytes()[:4] == b"MThd"

    def test_rhythm_to_midi_with_tuple(self):
        from accompy.pipeline import rhythm_to_midi

        md = rhythm_to_midi("| C | Am |", skeleton=(2, 2), tempo=120)
        assert md.to_bytes()[:4] == b"MThd"

    def test_rhythm_to_midi_waltz(self):
        from accompy.pipeline import rhythm_to_midi

        md = rhythm_to_midi(
            "| C | G | Am | F |",
            skeleton="waltz_quarters",
            tempo=100,
        )
        assert md.to_bytes()[:4] == b"MThd"
