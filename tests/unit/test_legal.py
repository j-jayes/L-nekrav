import datetime as dt
from decimal import Decimal

import pytest
import yaml

from lonekrav.core import legal
from lonekrav.core.legal import load_registry

D = dt.date

# Migrationsverket, "Lönekrav för arbetstillstånd" and "God försörjning", fetched 2026-10-21:
# (took effect, median, 90 %, 75 %, 80 %). The only place these literals are written outside the
# registry itself (research R6).
PUBLISHED = [
    (D(2026, 6, 16), 38300, 34470, 28725, 30640),
    (D(2025, 6, 17), 37100, 33390, 27825, 29680),
    (D(2024, 6, 18), 35600, 32040, 26700, 28480),
    (D(2023, 6, 20), 34200, 30780, 25650, 27360),
    (D(2022, 6, 21), 33200, 29880, 24900, 26560),
    (D(2021, 6, 22), 32400, 29160, 24300, 25920),
]


@pytest.fixture(scope="module")
def reg():
    return load_registry()


def test_every_row_has_a_source_and_checked_on(reg):
    rows = [*reg.medians, *reg.rules.values(), *reg.code_lists.values(), *reg.exemptions.values(),
            *reg.statements.values(), reg.median_publication_window]
    for row in rows:
        assert row.source.url.startswith("https://"), row
        assert row.source.checked_on, row


def test_medians_are_contiguous(reg):
    for a, b in zip(reg.medians, reg.medians[1:]):
        assert a.effective_to == b.effective_from - dt.timedelta(days=1)
    assert reg.medians[-1].effective_to is None


@pytest.mark.parametrize("took_effect,median,p90,p75,p80", PUBLISHED)
def test_amounts_match_migrationsverket(reg, took_effect, median, p90, p75, p80):
    m = reg.median_on(took_effect)
    assert (m.amount, m.effective_from) == (median, took_effect)
    assert m.scb_reference_year == took_effect.year - 1
    assert reg.threshold("salary_90", m) == p90
    assert reg.threshold("salary_75_exempt", m) == p75
    assert reg.threshold("transition_maintenance_80", m) == p80


def test_median_switches_on_the_day_it_takes_effect(reg):
    assert reg.median_on(D(2026, 6, 15)).amount == 37100
    assert reg.median_on(D(2026, 6, 16)).amount == 38300


def test_median_before_the_registry_starts_is_none(reg):
    assert reg.median_on(D(2021, 6, 21)) is None


def test_rounding_is_half_up():
    assert legal.round_half_up(Decimal("0.5")) == 1
    assert legal.round_half_up(Decimal("2.5")) == 3


def test_exempt_codes_follow_the_ordinance(reg):
    exempt = reg.codes_on("exempt_75", D(2026, 10, 21))
    assert len(exempt) == 27 and "3511" in exempt and "2512" not in exempt
    assert reg.codes_on("exempt_75", D(2026, 5, 31)) == {}
    assert set(reg.codes_on("banned", D(2026, 10, 21))) == {"5343"}
    assert set(reg.codes_on("partially_banned", D(2026, 10, 21))) == {"9210"}


def test_transition_rule(reg):
    t = reg.rules["transition_maintenance_80"]
    assert (t.effective_from, t.effective_to, t.permits_granted_before) == (
        D(2026, 6, 1), D(2026, 12, 1), D(2026, 6, 1))
    assert t.percent == Decimal(80)


def test_former_student_exemption_is_first_permit_only(reg):
    assert reg.exemptions["former_student_researcher"].first_permit_only
    assert not reg.exemptions["young_tech_company"].first_permit_only
    assert len(reg.exemptions) == 4


def test_timeline_is_ordered_and_complete(reg):
    events = reg.timeline()
    dates = [e.date for e in events if e.date]
    assert dates == sorted(dates)
    summaries = " ".join(e.summary for e in events)
    for needle in ("13 000", "80 %", "90 %", "38 300", "32 400"):
        assert needle in summaries
    assert any(e.date == D(2026, 12, 1) for e in events)  # transition ends
    assert all(e.source.checked_on for e in events)


def test_loader_names_a_row_without_a_source(tmp_path):
    raw = yaml.safe_load(legal.REGISTRY_FILE.read_text())
    del raw["medians"][0]["source"]
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(raw, allow_unicode=True))
    with pytest.raises(ValueError, match="medians"):
        load_registry.__wrapped__(bad)


@pytest.mark.parametrize("today,current", [
    (D(2026, 6, 23), True),   # this year's median is in the registry
    (D(2027, 6, 22), True),   # inside the publication window: not yet overdue
    (D(2027, 6, 23), False),  # past the window with no 2027 median
])
def test_registry_is_current(reg, today, current):  # FR-005a
    assert reg.registry_is_current(today) is current


def test_registry_holds_this_years_median():  # FR-005a: fails in CI if the June update is missed
    assert load_registry().registry_is_current(dt.date.today())
