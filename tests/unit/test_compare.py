"""Side-by-side comparison of 2–5 codes (spec Story 6, FR-027, FR-028)."""

import datetime as dt

import pytest
from pydantic import ValidationError

from lonekrav.core.compare import CompareRequest, compare
from lonekrav.core.eligibility import EligibilityRequest, evaluate
from lonekrav.core.search import HONEST_FIT

OFFER = {"monthly_salary_sek": 32000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": dt.date(2026, 10, 1), "decided_on": dt.date(2026, 10, 21)}


@pytest.fixture
def cmp(inputs, salaries):
    from lonekrav.core.profiles import build_profiles

    profiles = build_profiles(inputs)

    def run(**kw):
        return compare(CompareRequest(**kw), profiles=profiles, distributions=salaries[0],
                       age_bands=salaries[1])
    return run


def test_columns_in_request_order_with_sourced_descriptions(cmp):
    c = cmp(codes=["2512", "4430", "3511"])
    assert [col.code for col in c.columns] == ["2512", "4430", "3511"]
    by = {col.code: col for col in c.columns}
    assert {t.source.source for t in by["2512"].tasks_sv} == {"jobtech"}
    assert {t.source.source for t in by["4430"].tasks_sv} == {"scb_mis2012"}  # SCB where it has it
    assert by["3511"].tasks_en and {t.source.source for t in by["3511"].tasks_en} == {"esco"}
    assert by["2512"].latest.year == 2025 and by["2512"].latest.source_table == "TAB5932"
    assert [f.kind for f in by["3511"].legal_flags] == ["exempt_75"]
    assert by["3511"].threshold.rule_id == "salary_75_exempt"
    assert by["2512"].threshold.rule_id == "salary_90"


def test_offer_gives_each_column_the_same_answer_as_evaluate(cmp):
    c = cmp(codes=["2512", "3511"], offer=OFFER)
    for col in c.columns:
        assert col.eligibility == evaluate(EligibilityRequest(code=col.code, **OFFER))
    assert [col.eligibility.status for col in c.columns] == ["fail", "pass"]


def test_duplicates_are_dropped_before_counting(cmp):
    assert [col.code for col in cmp(codes=["2512", "2512", "3511"]).columns] == ["2512", "3511"]
    with pytest.raises(ValidationError, match="2–5"):
        CompareRequest(codes=["2512", "2512"])


@pytest.mark.parametrize("codes", [["2512"], ["0110", "1211", "1212", "2421", "2512", "3511"]])
def test_two_to_five_codes(codes):
    with pytest.raises(ValidationError, match="2–5"):
        CompareRequest(codes=codes)


def test_honest_fit_and_no_ranking_by_threshold(cmp):
    c = cmp(codes=["3511", "2512"], offer=OFFER)
    assert c.honest_fit == HONEST_FIT
    assert [col.code for col in c.columns] == ["3511", "2512"]  # as asked, not by threshold
