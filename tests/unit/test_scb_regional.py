"""SCB TAB5696: mean monthly salary per national area (Feature 005 US2, research R3)."""

import datetime as dt

from lonekrav.etl import scb_pxweb

T = dt.datetime(2026, 10, 23, tzinfo=dt.UTC)


def rows(fixtures):
    return {(r.code, r.year, r.region): r for r in
            scb_pxweb.parse_regional(fixtures / "pxweb/TAB5696.json", T)}


def test_national_row_for_2512(fixtures):
    s = rows(fixtures)[("2512", 2025, "SE")]
    assert (s.mean, s.mean_ci95, s.employees, s.region_name) == (55500, 940, 113100, "Sweden")
    assert s.source_table == "TAB5696" and s.reference_year == 2025 and s.fetched_at == T


def test_an_area_can_publish_a_mean_without_employees(fixtures):
    s = rows(fixtures)[("2512", 2025, "SE21")]
    assert s.mean == 48400 and s.employees is None and s.suppressed == ["employees"]
    assert s.region_name == "Småland and islands"


def test_every_area_every_year_and_0000_kept(fixtures):
    r = rows(fixtures)
    assert {k[2] for k in r} == {"SE", "SE11", "SE12", "SE21", "SE22", "SE23", "SE31", "SE32",
                                 "SE33"}
    assert {k[1] for k in r} == {2023, 2024, 2025}
    assert ("0000", 2025, "SE") in r  # all occupations, as for TAB5932


def test_suppressed_cells_stay_null(fixtures):
    suppressed = [x for x in rows(fixtures).values() if "mean" in x.suppressed]
    assert suppressed and all(x.mean is None and x.mean_ci95 is None for x in suppressed)
