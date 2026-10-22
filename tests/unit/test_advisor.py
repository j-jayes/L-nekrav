"""The advisor's input model and memo guard (Feature 003 FR-011, FR-016, research R10)."""

import pytest
from pydantic import ValidationError

from lonekrav.core.advisor import THIRD_PARTY_NOTICE, AdvisorRequest, finalise_memo
from lonekrav.core.eligibility import DISCLAIMER
from lonekrav.core.search import HONEST_FIT

OFFER = {"monthly_salary_sek": 52000.0, "fte_percent": 100.0, "application_type": "first_permit",
         "filed_on": "2026-10-01"}  # floats, as A2A data parts deliver them (research R7)


def test_ad_alone_is_enough():
    r = AdvisorRequest(ad="Backend developer")
    assert r.background is None and r.offer is None


def test_full_request_with_float_numbers():
    r = AdvisorRequest(ad="Backend developer", background="MSc, 5 years Python", offer=OFFER)
    assert r.offer.monthly_salary_sek == 52000 and isinstance(r.offer.monthly_salary_sek, int)


@pytest.mark.parametrize(("body", "field"), [
    ({"ad": ""}, "ad"),
    ({"ad": "x" * 20001}, "ad"),
    ({"ad": "x", "background": "y" * 5001}, "background"),
    ({"ad": "x", "offer": OFFER | {"fte_percent": 0}}, "fte_percent"),
])
def test_rejects(body, field):
    with pytest.raises(ValidationError) as e:
        AdvisorRequest(**body)
    assert field in str(e.value)


def test_guard_adds_what_the_model_left_out():
    memo = finalise_memo("Code 2512 fits.", ["search_occupations"])
    assert memo.startswith("Code 2512 fits.")
    assert HONEST_FIT in memo and DISCLAIMER in memo
    assert memo.rstrip().endswith(THIRD_PARTY_NOTICE)
    assert "not based on" not in memo


def test_guard_keeps_what_the_model_wrote():
    memo = finalise_memo(f"Code 2512 fits.\n\n{HONEST_FIT}\n\nThis is not legal advice.",
                         ["search_occupations"])
    assert memo.count(HONEST_FIT) == 1 and DISCLAIMER not in memo


def test_guard_flags_a_memo_with_no_tool_results():
    memo = finalise_memo("Probably 2512.", [])
    assert "not based on any Lönekrav result" in memo


def test_guard_is_idempotent():
    once = finalise_memo("Code 2512 fits.", [])
    assert finalise_memo(once, []) == once


def test_footer_stays_last_when_the_model_wrote_it_early():  # Copilot review on PR #3
    memo = finalise_memo(f"Code 2512 fits.\n\n{THIRD_PARTY_NOTICE}", [])
    assert HONEST_FIT in memo and DISCLAIMER in memo and "not based on" in memo
    assert memo.endswith(THIRD_PARTY_NOTICE) and memo.count(THIRD_PARTY_NOTICE) == 1
    assert finalise_memo(memo, []) == memo
