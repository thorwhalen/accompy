"""accompy.ireal: hostile charts decode in linear time; iReal entry points keep the tune's meter and tempo."""

import time

import pytest

from accompy.chord_parsers import parse_ireal_url as parse_to_sequence
from accompy.ireal import IrealTune, flatten_measures
from accompy.pipeline import _parse_ireal_url_robust

PREFIX = "1r34LbKcu7"
N = 40_000
#: Generous for a linear pass over ~160k characters; the quadratic versions took minutes.
TIME_LIMIT = 5.0


@pytest.mark.parametrize(
    "chart, bars",
    [
        ("{" * 22 + "C " + "}" * 22, 2),  # nested braces: no exponential expansion
        ("{C }" * N, 2 * N),  # many repeats
        ("<" * N + "C", 1),  # unclosed comments
        ("(" * N + "C", 1),  # unclosed alternate chords
        ("{" * N + "C", 1),  # unclosed repeats
        ("C }" * N, 2 * N),  # lone repeat ends
        ("{C |N1D }" + "|N2E" * N, N + 3),  # endings without a repeat to close
        ("C |r|" * N, 3 * N - 2),  # two-bar repeats (the first has one bar before it)
    ],
    ids=["nested", "repeats", "angles", "parens", "braces", "lone-ends", "endings", "r"],
)
def test_hostile_charts_decode_in_linear_time(chart, bars):
    start = time.perf_counter()
    assert len(flatten_measures(chart)) == bars
    assert time.perf_counter() - start < TIME_LIMIT


def test_tempo_unset_when_not_positive():
    assert IrealTune(bpm="0").tempo is None
    assert IrealTune(bpm="").tempo is None
    assert IrealTune(bpm="140").tempo == 140


def test_entry_points_keep_meter_and_ignore_zero_bpm():
    url = f"irealb://Waltz=X==Jazz Waltz=C=={PREFIX}[T34C^7 |D-7 G7 Z=Jazz=0=1"
    for cs in (parse_to_sequence(url), _parse_ireal_url_robust(url)):
        assert cs.time_signature == (3, 4)
        assert cs.chords == [("C^7", 3.0), ("D-7", 1.5), ("G7", 1.5)]
        assert cs.tempo == 120
