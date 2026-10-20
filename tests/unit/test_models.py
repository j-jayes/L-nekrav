import datetime as dt

import pytest
from pydantic import ValidationError

from lonekrav.core.models import (
    OccupationProfile,
    SalaryDistribution,
    SourceRef,
    Synonym,
    Text,
    dedupe_synonyms,
)

SCB = SourceRef(source="scb_structure", ref="ssyk-2012-koder.xlsx", url="https://www.scb.se/x")
FETCHED = dt.datetime(2026, 10, 20, tzinfo=dt.UTC)


def profile(**kw):
    base = {
        "code": "2512",
        "title_sv": "Mjukvaru- och systemutvecklare m.fl.",
        "title_en": "Software- and system developers",
        "isco_codes": ["2512"],
        "descriptions": [Text(lang="sv", kind="definition", text="Analyserar ...", source=SCB)],
        "sources": [SCB],
    }
    return OccupationProfile(**(base | kw))


def test_profile_accepts_minimal_valid_record():
    assert profile().code == "2512"


@pytest.mark.parametrize("code", ["251", "25120", "25a2", ""])
def test_profile_rejects_non_four_digit_code(code):
    with pytest.raises(ValidationError):
        profile(code=code)


def test_profile_requires_a_swedish_description():
    en_only = [Text(lang="en", kind="definition", text="Develops software", source=SCB)]
    with pytest.raises(ValidationError, match="Swedish description"):
        profile(descriptions=en_only)


def test_profile_requires_isco_code():
    with pytest.raises(ValidationError):
        profile(isco_codes=[])


def test_synonyms_dedupe_on_language_and_casefolded_label_keeping_first():
    syns = [
        Synonym(lang="sv", label="Systemutvecklare", source=SCB),
        Synonym(lang="sv", label="systemutvecklare", source=SCB.model_copy(update={"source": "jobtech"})),
        Synonym(lang="en", label="systemutvecklare", source=SCB),
    ]
    kept = dedupe_synonyms(syns)
    assert [(s.lang, s.label, s.source.source) for s in kept] == [
        ("sv", "Systemutvecklare", "scb_structure"),
        ("en", "systemutvecklare", "scb_structure"),
    ]


def salary(**kw):
    base = {"code": "2512", "year": 2025, "mean": 55500, "median": 53500, "p10": 39600, "p25": 46200,
                "p75": 62600, "p90": 72600, "source_table": "TAB5932", "reference_year": 2025,
                "fetched_at": FETCHED}
    return SalaryDistribution(**(base | kw))


def test_salary_lists_null_fields_as_suppressed():
    s = salary(p10=None, p10_ci95=None)
    assert "p10" in s.suppressed
    assert "median" not in s.suppressed


def test_salary_rejects_unordered_percentiles():
    with pytest.raises(ValidationError, match="2512 2025"):
        salary(p10=50000)


def test_salary_order_check_skips_when_a_percentile_is_suppressed():
    assert salary(p25=None, p10=47000).p10 == 47000


def test_salary_reference_year_must_equal_year():
    with pytest.raises(ValidationError):
        salary(reference_year=2024)
