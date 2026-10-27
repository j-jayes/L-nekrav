"""The age- and area-adjusted estimate (006 spec Story 2, FR-008–FR-010, research R2)."""

import datetime as dt

import pytest

from lonekrav.core.models import AgeBandSalary, RegionalSalary, SalaryDistribution
from lonekrav.core.salary import (
    AGE_BANDS_,
    BOTH_FORMULA,
    FORMULA,
    PERCENTILES,
    REGION_FORMULA,
    REGIONS,
    load_age_bands,
    load_distributions,
    load_regional,
    payload,
)

ON = dt.date(2026, 10, 27)
T = dt.datetime(2026, 10, 21)
FIGURES = {"p10": 41000, "p25": 47700, "median": 56200, "p75": 66700, "p90": 77800}


def dist(year=2025, **over):
    return SalaryDistribution(code="2511", year=year, mean=58500, **{**FIGURES, **over},
                              source_table="TAB5932", reference_year=year, fetched_at=T)


def age(band, mean, year=2025):
    return AgeBandSalary(code="2511", year=year, age_band=band, mean_monthly=mean, headcount=None,
                         source_table="TAB5844", reference_year=year, fetched_at=T)


def area(region, mean, year=2025):
    return RegionalSalary(code="2511", year=year, region=region, region_name=region, mean=mean,
                          employees=None, source_table="TAB5696", reference_year=year, fetched_at=T)


AGES = [age("25-34", 50200), age("all", 58500)]
AREAS = [area("SE", 58500), area("SE11", 63900)]


def make(dists=None, ages=AGES, areas=AREAS, **kw):
    return payload("2511", on=ON, distributions=dists or [dist()], age_bands=ages,
                   regional=areas, **kw)


def test_both_factors_scale_every_percentile():
    s = make(age_band="25-34", region="SE11").simulated
    factor = (50200 / 58500) * (63900 / 58500)
    assert (s.p25, s.p75) == (round(47700 * factor), round(66700 * factor))  # ≈ 44 711–62 520
    assert s.applied == ["age", "region"] and s.left_out == []
    assert s.formula == BOTH_FORMULA and "independent" in s.formula
    assert {i.table for i in s.inputs} == {"TAB5932", "TAB5844", "TAB5696"}
    assert s.is_simulated is True and (s.age_band, s.region) == ("25-34", "SE11")


def test_area_only():
    s = make(region="SE11").simulated
    assert s.applied == ["region"] and s.age_band is None and s.formula == REGION_FORMULA
    assert s.median == round(56200 * 63900 / 58500)
    assert {i.table for i in s.inputs} == {"TAB5932", "TAB5696"}


def test_age_only_keeps_the_existing_formula():
    s = make(age_band="25-34").simulated
    assert s.applied == ["age"] and s.formula == FORMULA
    assert {i.table for i in s.inputs} == {"TAB5932", "TAB5844"}


def test_a_suppressed_sweden_mean_leaves_the_area_out_with_a_reason():
    p = make(areas=[area("SE", None), area("SE11", 63900)], age_band="25-34", region="SE11")
    s = p.simulated
    assert s.applied == ["age"] and s.formula == FORMULA
    assert [lo.factor for lo in s.left_out] == ["region"]
    assert "Sweden" in s.left_out[0].reason and "TAB5696" in s.left_out[0].reason


def test_a_suppressed_age_mean_leaves_age_out():
    s = make(ages=[age("25-34", None), age("all", 58500)], age_band="25-34", region="SE11").simulated
    assert s.applied == ["region"] and [lo.factor for lo in s.left_out] == ["age"]
    assert "25-34" in s.left_out[0].reason


def test_no_regional_row_for_the_year_names_the_table_and_year():
    p = make(areas=[area("SE", 58500, 2024), area("SE11", 63900, 2024)], region="SE11")
    assert p.simulated is None
    assert "TAB5696" in p.estimate_note and "2025" in p.estimate_note


def test_neither_factor_gives_no_estimate_and_a_note():
    p = make(ages=[], areas=[], age_band="25-34", region="SE11")
    assert p.simulated is None and "TAB5844" in p.estimate_note and "TAB5696" in p.estimate_note


def test_no_p25_and_no_p75_gives_no_estimate():
    p = make(dists=[dist(p25=None, p75=None)], age_band="25-34")
    assert p.simulated is None and "P25" in p.estimate_note and "P75" in p.estimate_note


def test_no_estimate_requested_means_no_note():
    p = make()
    assert p.simulated is None and p.estimate_note is None


def test_unknown_region_is_refused():
    with pytest.raises(ValueError, match="region"):
        make(region="SE99")


def test_every_estimate_on_the_committed_data_is_the_formula_or_absent_with_a_reason():
    """SC-003: every code × 7 age options × 9 area options."""
    dists, ages, areas = load_distributions(), load_age_bands(), load_regional()
    by_code = {}
    for rows, key in ((dists, "d"), (ages, "a"), (areas, "r")):
        for r in rows:
            by_code.setdefault(r.code, {"d": [], "a": [], "r": []})[key].append(r)
    for code, rows in by_code.items():
        if not rows["d"]:
            continue
        d = max(rows["d"], key=lambda x: x.year)
        a = {x.age_band: x.mean_monthly for x in rows["a"] if x.year == d.year}
        r = {x.region: x.mean for x in rows["r"] if x.year == d.year}
        for band in (None, *AGE_BANDS_):
            for region in (None, *REGIONS):
                p = payload(code, on=ON, age_band=band, region=region, distributions=rows["d"],
                            age_bands=rows["a"], regional=rows["r"])
                if band is None and region is None:
                    assert p.simulated is None and p.estimate_note is None
                    continue
                s = p.simulated
                if s is None:
                    assert p.estimate_note
                    continue
                factor = 1.0
                if "age" in s.applied:
                    factor *= a[band] / a["all"]
                if "region" in s.applied:
                    factor *= r[region] / r["SE"]
                for n in PERCENTILES:
                    v = getattr(d, n)
                    assert getattr(s, n) == (None if v is None else round(v * factor))
                assert s.is_simulated is True
