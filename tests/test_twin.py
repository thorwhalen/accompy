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


@needs_fixtures
def test_order_matters():
    case = next(c for c in CASES if c["fn"] == "generate_events" and c["expected"])
    assert not same(case["expected"], case["expected"][::-1])


@pytest.mark.skipif(
    not (REPO_ROOT / _codegen.TS_DATA_PATH).exists(),
    reason="no ts/ (installed package)",
)
def test_generated_ts_tables_are_current():
    committed = (REPO_ROOT / _codegen.TS_DATA_PATH).read_text(encoding="utf-8")
    assert committed == _codegen.render_ts(), (
        "ts/src/data.generated.ts is stale: run `python -m accompy._codegen`"
    )
