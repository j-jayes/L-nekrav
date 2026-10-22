"""Eligibility rules (spec Story 1, FR-003–FR-012). Amounts and dates are written out here because
this is a test of the rules themselves (Principle II allows it in registry and eligibility tests);
each one is checked against Migrationsverket in research R6."""

import datetime as dt

import pytest
from pydantic import ValidationError

from lonekrav.core.eligibility import EligibilityRequest, UnknownCode, evaluate

D = dt.date
GRANTED_OLD = D(2026, 1, 10)  # a permit granted under the earlier rules
KNOWN = {"2512", "3511", "5343", "9210"}


def req(**kw) -> EligibilityRequest:
    base = {"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100,
            "application_type": "first_permit", "filed_on": D(2026, 6, 16),
            "decided_on": D(2026, 7, 1)}
    return EligibilityRequest(**(base | kw))


def ev(**kw):
    return evaluate(req(**kw), known_codes=KNOWN)


# --- request validation (T022) ---------------------------------------------------------------

@pytest.mark.parametrize("kw,field", [
    ({"fte_percent": 0}, "fte_percent"),
    ({"fte_percent": 101}, "fte_percent"),
    ({"monthly_salary_sek": 0}, "monthly_salary_sek"),
    ({"code": "25"}, "code"),
    ({"application_type": "extension"}, "current_permit_granted_on"),
    ({"current_permit_granted_on": GRANTED_OLD}, "current_permit_granted_on"),
    ({"decided_on": D(2026, 6, 1)}, "decided_on"),
    ({"exemptions": ["no_such_exemption"]}, "exemptions"),
    ({"exemptions": ["young_tech_company", "young_tech_company"]}, "exemptions"),
    ({"application_type": "extension", "current_permit_granted_on": GRANTED_OLD,
      "exemptions": ["former_student_researcher"]}, "exemptions"),
])
def test_invalid_requests_name_the_field(kw, field):
    with pytest.raises(ValidationError, match=field):
        req(**kw)


def test_unknown_code_is_refused():
    with pytest.raises(UnknownCode, match="1234"):
        evaluate(req(code="1234"), known_codes=KNOWN)


def test_decision_date_defaults_to_today():
    r = EligibilityRequest(code="2512", monthly_salary_sek=40000, fte_percent=100,
                           application_type="first_permit", filed_on=D(2026, 6, 16))
    assert r.decided_on == dt.date.today()


# --- rule selection (T023): Story 1 scenarios 1–12 and the edge cases --------------------------

def test_s1_first_permit_on_the_day_the_new_median_applies():
    a = ev()
    assert (a.status, a.rule_id, a.threshold_sek, a.margin_sek) == ("pass", "salary_90", 34470, 5530)
    assert a.median.amount == 38300 and a.median.scb_reference_year == 2025


def test_s2_day_before_uses_the_previous_median():
    a = ev(filed_on=D(2026, 6, 15))
    assert (a.threshold_sek, a.median.amount) == (33390, 37100)


def test_s3_exempt_code():
    a = ev(code="3511", filed_on=D(2026, 10, 21), decided_on=D(2026, 10, 21))
    assert (a.rule_id, a.threshold_sek) == ("salary_75_exempt", 28725)


def test_s4_banned_code_is_not_permitted_whatever_the_salary():
    a = ev(code="5343", monthly_salary_sek=100000)
    assert a.status == "not_permitted"
    assert a.threshold_sek is None and a.margin_sek is None
    assert any("2026605" in s.url for s in a.sources)


def test_s5_9210_partial_ban_warning_and_75_percent():
    a = ev(code="9210")
    assert a.rule_id == "salary_75_exempt"
    assert [w.kind for w in a.warnings] == ["partial_ban"]
    assert "berry" in a.warnings[0].message


@pytest.mark.parametrize("filed,rule", [
    (D(2026, 11, 30), "transition_maintenance_80"),
    (D(2026, 12, 1), "transition_maintenance_80"),  # the window is inclusive
    (D(2026, 12, 2), "salary_90"),
])
def test_s6_transitional_extensions(filed, rule):
    a = ev(application_type="extension", current_permit_granted_on=GRANTED_OLD, filed_on=filed,
           decided_on=filed + dt.timedelta(days=30))
    assert a.rule_id == rule


def test_s7_part_time_does_not_reduce_the_threshold():
    full, part = ev(), ev(fte_percent=80)
    assert part.threshold_sek == full.threshold_sek
    w = [w for w in part.warnings if w.kind == "part_time"]
    assert w and "employees" in w[0].source.url


def test_s8_stale_median_warning_names_the_median_used():
    a = ev(filed_on=D(2027, 6, 20), decided_on=D(2027, 6, 20))
    w = [w for w in a.warnings if w.kind == "stale_median"]
    assert w and "38 300" in w[0].message


def test_s9_declared_exemption():
    a = ev(exemptions=["young_tech_company"])
    assert (a.rule_id, a.threshold_sek) == ("salary_75_exempt", 28725)
    assert "young tech" in a.reason.lower()
    assert any("lonekrav" in s.url for s in a.sources)


def test_s10_exempt_code_on_a_transitional_extension_gets_80_not_75():
    a = ev(code="3511", application_type="extension", current_permit_granted_on=GRANTED_OLD,
           filed_on=D(2026, 11, 30), decided_on=D(2026, 12, 20))
    assert (a.rule_id, a.threshold_sek) == ("transition_maintenance_80", 30640)


def test_s11_filed_before_june_decided_after_uses_the_filing_date_median():
    a = ev(filed_on=D(2026, 5, 20), decided_on=D(2026, 6, 20))
    assert (a.rule_id, a.threshold_sek) == ("salary_90", 33390)


def test_s12_extension_of_a_permit_granted_after_june_is_not_transitional():
    a = ev(application_type="extension", current_permit_granted_on=D(2026, 7, 10),
           filed_on=D(2026, 11, 30), decided_on=D(2026, 12, 20))
    assert a.rule_id == "salary_90"


@pytest.mark.parametrize("kw", [
    {"filed_on": D(2026, 5, 1), "decided_on": D(2026, 5, 31)},  # first permit decided too early
    {"application_type": "extension", "current_permit_granted_on": D(2025, 1, 1),
     "filed_on": D(2026, 5, 31), "decided_on": D(2026, 6, 20)},  # extension filed too early
])
def test_earlier_decisions_are_out_of_scope(kw):
    a = ev(**kw)
    assert a.status == "out_of_scope" and a.threshold_sek is None
    assert "Blue Card" in a.reason


def test_banned_beats_a_declared_exemption():
    assert ev(code="5343", exemptions=["young_tech_company"]).status == "not_permitted"


def test_salary_exactly_at_the_threshold_passes():
    a = ev(monthly_salary_sek=34470)
    assert (a.status, a.margin_sek) == ("pass", 0)


def test_below_the_threshold_fails_with_a_negative_margin():
    a = ev(monthly_salary_sek=34000)
    assert (a.status, a.margin_sek) == ("fail", -470)
    assert a.margin_percent == pytest.approx(-1.4, abs=0.05)


# --- answer content (T024) -------------------------------------------------------------------

def test_every_answer_carries_the_disclaimer():
    for a in (ev(), ev(code="5343"), ev(filed_on=D(2026, 5, 1), decided_on=D(2026, 5, 31))):
        assert "collective agreement" in a.disclaimer and "not legal advice" in a.disclaimer


def test_sources_cover_the_rule_the_median_and_what_decided_it():
    a = ev(code="3511")
    urls = {s.url for s in a.sources}
    assert any("lonekrav-for-arbetstillstand" in u for u in urls)  # rule and median
    assert any("2026605" in u for u in urls)  # the exempt list that decided it
    assert all(s.checked_on for s in a.sources)


def test_every_warning_has_a_source():
    a = ev(code="9210", fte_percent=50, filed_on=D(2027, 6, 20), decided_on=D(2027, 6, 20))
    assert {w.kind for w in a.warnings} == {"partial_ban", "part_time", "stale_median"}
    assert all(w.source.url for w in a.warnings)
