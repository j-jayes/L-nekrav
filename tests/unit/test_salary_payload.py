"""Salary payload for one occupation (spec Story 5, FR-024–FR-026)."""

import datetime as dt

import pytest

from lonekrav.core.legal import load_registry
from lonekrav.core.salary import FORMULA, payload

ON = dt.date(2026, 10, 21)


def make(salaries, code, **kw):
    dists, ages = salaries
    return payload(code, on=ON, distributions=dists, age_bands=ages,
                   titles={code: ("sv", "en")}, **kw)


def test_official_figures_are_passed_through_exactly(salaries):
    p = make(salaries, "2512")
    d = next(d for d in p.distributions if d.year == 2025)
    stored = next(r for r in salaries[0] if r.code == "2512" and r.year == 2025)
    assert d == stored
    assert (d.source_table, d.reference_year) == ("TAB5932", 2025)
    assert p.age_bands and all(a.year == 2025 for a in p.age_bands)
    assert not p.no_occupation_data and p.simulated is None


def test_threshold_lines_come_from_the_registry(salaries):
    reg = load_registry()
    median = reg.median_on(ON)
    lines = {t.rule_id: t for t in make(salaries, "2512").thresholds}
    assert lines["salary_90"].amount_sek == reg.threshold("salary_90", median)
    assert lines["salary_75_exempt"].amount_sek == reg.threshold("salary_75_exempt", median)
    assert make(salaries, "2512").applicable_rule_id == "salary_90"
    assert make(salaries, "3511").applicable_rule_id == "salary_75_exempt"
    assert make(salaries, "5343").applicable_rule_id is None  # banned: no threshold applies


def test_suppressed_cells_stay_null(salaries):
    d = next(d for d in salaries[0] if d.suppressed)
    p = make(salaries, d.code)
    same = next(x for x in p.distributions if x.year == d.year)
    assert same.suppressed == d.suppressed
    assert all(getattr(same, f) is None for f in d.suppressed)


def test_simulated_age_band_percentiles(salaries):
    p = make(salaries, "2512", age_band="25-34")
    s = p.simulated
    dists, ages = salaries
    d = next(r for r in dists if r.code == "2512" and r.year == s.year)
    band = next(a for a in ages if a.code == "2512" and a.year == s.year and a.age_band == "25-34")
    every = next(a for a in ages if a.code == "2512" and a.year == s.year and a.age_band == "all")
    assert s.is_simulated is True and s.formula == FORMULA
    assert s.median == round(d.median * band.mean_monthly / every.mean_monthly)
    assert {i.table for i in s.inputs} == {"TAB5932", "TAB5844"}


def test_a_null_input_gives_a_null_simulated_value(salaries):
    dists, ages = salaries
    code = next(d.code for d in dists if d.suppressed and d.year == 2025 and d.median is not None)
    s = make(salaries, code, age_band="25-34").simulated
    missing = next(d for d in dists if d.code == code and d.year == s.year).suppressed
    assert all(getattr(s, f) is None for f in missing)


def test_code_without_salary_rows(salaries):
    p = make(salaries, "9999")
    assert p.no_occupation_data and p.distributions == [] and p.thresholds


def test_unknown_age_band_is_refused(salaries):
    with pytest.raises(ValueError, match="age_band"):
        make(salaries, "2512", age_band="12-17")
