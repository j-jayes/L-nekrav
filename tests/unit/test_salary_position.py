"""Where a number sits among SCB's published percentiles (006 spec Story 1, FR-003, FR-004)."""

import datetime as dt

import pytest

from lonekrav.core.models import SalaryDistribution
from lonekrav.core.salary import PERCENTILES, load_distributions, position

# 2511 in 2025, as SCB publishes it (TAB5932)
FIGURES = {"p10": 41000, "p25": 47700, "median": 56200, "p75": 66700, "p90": 77800}


def dist(**over):
    values = {**FIGURES, **over}
    return SalaryDistribution(code="2511", year=2025, mean=58500, **values, source_table="TAB5932",
                              reference_year=2025, fetched_at=dt.datetime(2026, 10, 21))


def names(p):
    return (p.lower and p.lower.name, p.upper and p.upper.name, p.at and p.at.name)


@pytest.mark.parametrize("amount, expected", [
    (30000, (None, "p10", None)),
    (45000, ("p10", "p25", None)),
    (50000, ("p25", "median", None)),
    (60000, ("median", "p75", None)),
    (70000, ("p75", "p90", None)),
    (90000, ("p90", None, None)),
    (56200, (None, None, "median")),
])
def test_each_bracket(amount, expected):
    p = position(amount, dist())
    assert names(p) == expected
    assert (p.amount_sek, p.year, p.source_table) == (amount, 2025, "TAB5932")
    assert not p.missing and not p.no_data


def test_bracket_values_are_the_published_ones():
    p = position(60000, dist())
    assert (p.lower.value_sek, p.upper.value_sek) == (56200, 66700)


def test_a_suppressed_bound_widens_the_bracket_and_is_named():
    p = position(50000, dist(p25=None))
    assert names(p) == ("p10", "median", None)
    assert p.missing == ["p25"]


def test_a_suppressed_outer_percentile_is_named_too():
    p = position(30000, dist(p10=None))
    assert names(p) == (None, "p25", None)
    assert p.missing == ["p10"]


def test_no_published_percentile_gives_no_position():
    p = position(50000, dist(**dict.fromkeys(PERCENTILES)))
    assert p.no_data and names(p) == (None, None, None)


def test_every_returned_value_is_copied_from_scb():
    """SC-002: over every committed distribution, the bracket holds only published values."""
    latest = {}
    for d in load_distributions():
        if d.year >= latest.get(d.code, d).year:
            latest[d.code] = d
    for d in latest.values():
        published = {getattr(d, n) for n in PERCENTILES} - {None}
        for amount in range(20000, 120001, 1000):
            p = position(amount, d)
            for ref in (p.lower, p.upper, p.at):
                if ref:
                    assert ref.value_sek == getattr(d, ref.name) and ref.value_sek in published
            if p.lower:
                assert p.lower.value_sek < amount
            if p.upper:
                assert p.upper.value_sek > amount
