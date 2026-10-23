import datetime as dt

import pytest
from pydantic import ValidationError

from lonekrav.core.models import RegionalSalary, YearlyAds

FETCHED = dt.datetime(2026, 10, 23, tzinfo=dt.UTC)


def regional(**kw):
    base = {"code": "2512", "year": 2025, "region": "SE21", "region_name": "Småland and islands",
            "mean": 48400, "mean_ci95": 1960, "employees": None, "source_table": "TAB5696",
            "reference_year": 2025, "fetched_at": FETCHED}
    return RegionalSalary(**(base | kw))


def test_regional_mean_and_employees_are_suppressed_independently():
    assert regional().suppressed == ["employees"]
    assert regional(mean=None, mean_ci95=None, employees=900).suppressed == ["mean"]


def test_regional_reference_year_must_equal_year():
    with pytest.raises(ValidationError):
        regional(reference_year=2024)


def test_regional_only_from_tab5696():
    with pytest.raises(ValidationError):
        regional(source_table="TAB4185")


def test_yearly_ads_zero_is_a_count():
    assert YearlyAds(concept_id="DJh5_yyF_hEM", year=2016, ads=0, built_at=FETCHED).ads == 0


@pytest.mark.parametrize("kw", [{"ads": -1}, {"year": 2015}])
def test_yearly_ads_rejects_negative_counts_and_years_before_2016(kw):
    with pytest.raises(ValidationError):
        YearlyAds(**({"concept_id": "x", "year": 2020, "ads": 1, "built_at": FETCHED} | kw))
