"""The shared service every protocol adapter calls (Feature 003 FR-002, data-model.md)."""

import datetime as dt

import pytest

from lonekrav.core.eligibility import EligibilityRequest, UnknownCode

OFFER = {"monthly_salary_sek": 40000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": "2026-06-16", "decided_on": "2026-07-01"}


@pytest.fixture
def service(fixture_engine, salaries):
    from lonekrav.core.service import Service

    engine, profiles = fixture_engine
    return Service(engine=engine, profiles=profiles, distributions=salaries[0],
                   age_bands=salaries[1])


def test_occupation_has_flags_and_no_ilo_text(service):
    from lonekrav.core.models import Text
    from lonekrav.core.profiles import REFS

    ilo = Text(lang="en", kind="definition", text="ILO definition", source=REFS["ilo_isco08"])
    stored = service.profiles["3511"]
    service.profiles["3511"] = stored.model_copy(
        update={"descriptions": [*stored.descriptions, ilo]})  # as attach_ilo adds at index time
    p = service.occupation("3511")
    assert p.legal_flags and p.legal_flags[0].kind == "exempt_75"
    assert ilo not in p.descriptions and len(p.descriptions) == len(stored.descriptions)


def test_occupation_unknown_code(service):
    with pytest.raises(UnknownCode, match="9999"):
        service.occupation("9999")


def test_salary_defaults_to_today_and_carries_titles(service):
    pay = service.salary("2512")
    assert pay.title_en == "Software- and system developers" and pay.title_sv
    assert all(t.on == dt.date.today() for t in pay.thresholds)


def test_salary_errors(service):
    with pytest.raises(UnknownCode):
        service.salary("9999")
    with pytest.raises(ValueError, match="age_band"):
        service.salary("2512", age_band="12-17")


def test_eligibility_unknown_code(service):
    with pytest.raises(UnknownCode):
        service.eligibility(EligibilityRequest(code="1234", **OFFER))


def test_compare_names_the_unknown_code(service):
    from lonekrav.core.compare import CompareRequest

    with pytest.raises(UnknownCode, match="1234"):
        service.compare(CompareRequest(codes=["2512", "1234"]))
    assert [c.code for c in service.compare(CompareRequest(codes=["3511", "2512"])).columns] == [
        "3511", "2512"]


def test_parse_ad_uses_kblab(service, fixtures):
    from lonekrav.core.adparse import AdText, parse

    ad = (fixtures / "ads/en1_backend.txt").read_text()
    assert service.parse_ad(AdText(text=ad)) == parse(ad, service.engine.embedders["kblab"])


def test_timeline_is_the_registry_timeline(service):
    from lonekrav.core.legal import load_registry

    assert service.timeline() == load_registry().timeline()


def test_search_runs_core_search(service):
    from lonekrav.core.search import SearchRequest, run

    req = SearchRequest(text="mjukvaruutvecklare")
    assert service.search(req) == run(req, service.engine)
