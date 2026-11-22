"""The TypeScript twin's contract, Python side: golden cases and generated tables.

``fixtures/cases.json`` is run here and by ``ts/src/fixtures.test.ts``; the tables in
``ts/src/data.generated.ts`` must be what :mod:`accompy._codegen` renders now.
"""

import pytest

from accompy import _codegen
from accompy._fixtures import (
    CASES_PATH,
    REPO_ROOT,
    TWIN_FUNCTIONS,
    load,
    run_case,
    same,
)

DATA = load() if (REPO_ROOT / CASES_PATH).exists() else {"functions": [], "cases": []}
CASES = DATA["cases"]
needs_fixtures = pytest.mark.skipif(
    not CASES, reason="fixtures/cases.json not present (installed package)"
)


@needs_fixtures
@pytest.mark.parametrize(
    "case", CASES, ids=lambda c: f"{c['fn']}{c.get('args')!r}"[:80]
)
def test_case(case):
    assert same(run_case(case), case["expected"])


@needs_fixtures
def test_cases_cover_exactly_the_twin_functions():
    assert DATA["functions"] == list(TWIN_FUNCTIONS)
    assert {c["fn"] for c in CASES} == set(TWIN_FUNCTIONS)


def _dyadic(x) -> bool:
    return not isinstance(x, float) or (x * 2**10).is_integer()


def _numbers(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        yield value
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _numbers(v)


@needs_fixtures
def test_skeleton_durations_are_dyadic():
    """Python 3.10's sum() and 3.12's (compensated) differ on inexact floats; dyadic ones agree."""
    for case in CASES:
        if case["fn"] in ("apply_skeleton", "resolve_skeleton"):
            skeleton = case["args"][-1]  # chord durations are subtracted, not sum()med
            assert all(_dyadic(x) for x in _numbers(skeleton)), case


@pytest.mark.skipif(
    not (REPO_ROOT / _codegen.TS_DATA_PATH).exists(),
    reason="no ts/ (installed package)",
)
def test_generated_ts_tables_are_current():
    committed = (REPO_ROOT / _codegen.TS_DATA_PATH).read_text(encoding="utf-8")
    assert committed == _codegen.render_ts(), (
        "ts/src/data.generated.ts is stale: run `python -m accompy._codegen`"
    )


def test_cases_do_not_depend_on_the_global_chord_resolver():
    from accompy import _fixtures
    from accompy.chord_resolution import get_chord_resolver, set_chord_resolver

    cases = [c for c in _fixtures.load()["cases"] if c["fn"] == "generate_events"]
    previous = get_chord_resolver()
    set_chord_resolver(lambda symbol: [60])
    try:
        for case in cases:
            assert _fixtures.same(_fixtures.run_case(case), case["expected"]), case["args"]
    finally:
        set_chord_resolver(previous)
