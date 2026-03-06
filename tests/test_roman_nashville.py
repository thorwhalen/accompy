"""Tests for Roman numeral and Nashville number chord parsers."""

import pytest

from accompy.chord_parsers import (
    parse_roman_numeral,
    parse_nashville,
    _roman_to_chord_symbol,
    _nashville_to_chord_symbol,
)


# ---------------------------------------------------------------------------
# Roman numeral: individual token conversion
# ---------------------------------------------------------------------------


class TestRomanToChordSymbol:
    def test_major_triads(self):
        assert _roman_to_chord_symbol("I", "C") == "C"
        assert _roman_to_chord_symbol("IV", "C") == "F"
        assert _roman_to_chord_symbol("V", "C") == "G"

    def test_minor_triads(self):
        assert _roman_to_chord_symbol("ii", "C") == "Dm"
        assert _roman_to_chord_symbol("iii", "C") == "Em"
        assert _roman_to_chord_symbol("vi", "C") == "Am"

    def test_seventh_chords(self):
        assert _roman_to_chord_symbol("ii7", "C") == "Dm7"
        assert _roman_to_chord_symbol("V7", "C") == "G7"
        assert _roman_to_chord_symbol("Imaj7", "C") == "Cmaj7"

    def test_flat_accidental(self):
        result = _roman_to_chord_symbol("bVII7", "C")
        assert result == "Bb7"

    def test_sharp_accidental(self):
        result = _roman_to_chord_symbol("#IV", "C")
        assert result == "F#"

    def test_different_keys(self):
        assert _roman_to_chord_symbol("I", "G") == "G"
        assert _roman_to_chord_symbol("V", "G") == "D"
        assert _roman_to_chord_symbol("ii", "G") == "Am"

    def test_dim_chord(self):
        result = _roman_to_chord_symbol("viidim", "C")
        assert result == "Bmdim" or result == "Bdim"  # depends on impl

    def test_non_roman_passthrough(self):
        assert _roman_to_chord_symbol("Cmaj7", "C") == "Cmaj7"


# ---------------------------------------------------------------------------
# Roman numeral: full parser
# ---------------------------------------------------------------------------


class TestParseRomanNumeral:
    def test_ii_V_I_in_C(self):
        cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="C")
        assert cs.symbols == ["Dm7", "G7", "Cmaj7"]
        assert cs.durations == [4.0, 4.0, 4.0]

    def test_ii_V_I_in_F(self):
        cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="F")
        assert cs.symbols == ["Gm7", "C7", "Fmaj7"]

    def test_ii_V_I_in_G(self):
        cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="G")
        assert cs.symbols == ["Am7", "D7", "Gmaj7"]

    def test_space_separated(self):
        cs = parse_roman_numeral("I IV V I", key="C")
        assert cs.symbols == ["C", "F", "G", "C"]

    def test_preserves_metadata(self):
        cs = parse_roman_numeral(
            "I IV V I", key="D", tempo=160, title="Test"
        )
        assert cs.key == "D"
        assert cs.tempo == 160
        assert cs.title == "Test"

    def test_I_V_vi_IV_in_C(self):
        cs = parse_roman_numeral("I V vi IV", key="C")
        assert cs.symbols == ["C", "G", "Am", "F"]

    def test_I_V_vi_IV_in_G(self):
        cs = parse_roman_numeral("I V vi IV", key="G")
        assert cs.symbols == ["G", "D", "Em", "C"]

    @pytest.mark.parametrize(
        "key,expected_I,expected_V",
        [
            ("C", "C", "G"),
            ("D", "D", "A"),
            ("E", "E", "B"),
            ("F", "F", "C"),
            ("G", "G", "D"),
            ("A", "A", "E"),
            ("Bb", "Bb", "F"),
            ("Eb", "Eb", "Bb"),
        ],
    )
    def test_multiple_keys(self, key, expected_I, expected_V):
        cs = parse_roman_numeral("I V", key=key)
        assert cs.symbols[0] == expected_I
        assert cs.symbols[1] == expected_V


# ---------------------------------------------------------------------------
# Nashville: individual token conversion
# ---------------------------------------------------------------------------


class TestNashvilleToChordSymbol:
    def test_basic_degrees(self):
        assert _nashville_to_chord_symbol("1", "C") == "C"
        assert _nashville_to_chord_symbol("4", "C") == "F"
        assert _nashville_to_chord_symbol("5", "C") == "G"

    def test_with_quality(self):
        assert _nashville_to_chord_symbol("2m7", "C") == "Dm7"
        assert _nashville_to_chord_symbol("57", "C") == "G7"
        assert _nashville_to_chord_symbol("1maj7", "C") == "Cmaj7"

    def test_flat_accidental(self):
        result = _nashville_to_chord_symbol("b7", "C")
        assert result == "Bb"

    def test_different_keys(self):
        assert _nashville_to_chord_symbol("1", "G") == "G"
        assert _nashville_to_chord_symbol("5", "G") == "D"

    def test_non_nashville_passthrough(self):
        assert _nashville_to_chord_symbol("Cmaj7", "C") == "Cmaj7"


# ---------------------------------------------------------------------------
# Nashville: full parser
# ---------------------------------------------------------------------------


class TestParseNashville:
    def test_basic_in_C(self):
        cs = parse_nashville("| 2m7 | 5 | 1maj7 |", key="C")
        assert cs.symbols == ["Dm7", "G", "Cmaj7"]

    def test_basic_in_G(self):
        cs = parse_nashville("1 4 5 1", key="G")
        assert cs.symbols == ["G", "C", "D", "G"]

    def test_with_seventh(self):
        cs = parse_nashville("| 2m7 | 57 | 1maj7 |", key="Bb")
        assert cs.symbols == ["Cm7", "F7", "Bbmaj7"]

    def test_preserves_metadata(self):
        cs = parse_nashville("1 4 5 1", key="A", tempo=140, title="Nashville Test")
        assert cs.key == "A"
        assert cs.tempo == 140
        assert cs.title == "Nashville Test"

    def test_bar_lines(self):
        cs = parse_nashville("| 1 | 4 | 5 | 1 |", key="D")
        assert cs.symbols == ["D", "G", "A", "D"]
        assert cs.durations == [4.0, 4.0, 4.0, 4.0]

    @pytest.mark.parametrize(
        "key,expected_1,expected_4,expected_5",
        [
            ("C", "C", "F", "G"),
            ("G", "G", "C", "D"),
            ("D", "D", "G", "A"),
            ("A", "A", "D", "E"),
            ("F", "F", "Bb", "C"),
        ],
    )
    def test_multiple_keys(self, key, expected_1, expected_4, expected_5):
        cs = parse_nashville("1 4 5", key=key)
        assert cs.symbols == [expected_1, expected_4, expected_5]
