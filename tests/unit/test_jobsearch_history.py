"""Yearly ads per JobTech occupation group from the historical ads API (Feature 005 US3, R4)."""

import datetime as dt
import json

import pytest

from lonekrav.etl import jobsearch
from lonekrav.etl.http import meta_path

T = dt.datetime(2026, 10, 23, tzinfo=dt.UTC)
CONCEPT = "DJh5_yyF_hEM"


def test_years_are_full_years_from_2016():
    assert jobsearch.years(dt.date(2026, 10, 23)) == list(range(2016, 2026))
    assert jobsearch.years(dt.date(2027, 1, 2))[-1] == 2026


def test_parse_year_reads_the_total(fixtures):
    assert jobsearch.parse_year(fixtures / "jobsearch/history_2512_2016.json") == 16406
    assert jobsearch.parse_year(fixtures / "jobsearch/history_2512_2025.json") == 30304


def cached(dest, body):
    """A history file as cached_get leaves it: the body and its .meta.json."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body)
    meta_path(dest).write_text(json.dumps({"url": "u", "fetched_at": T.isoformat(), "sha256": "x"}))


@pytest.fixture
def raw(fixtures, tmp_path):
    for y in (2016, 2025):
        cached(jobsearch.path_for(tmp_path, CONCEPT, y),
               (fixtures / f"jobsearch/history_2512_{y}.json").read_text())
    cached(jobsearch.path_for(tmp_path, "zero_concept", 2016),
           json.dumps({"total": {"value": 0}, "positions": 0}))
    return tmp_path


def test_build_history_keeps_zero_as_a_count(raw):
    rows = jobsearch.build_history(raw, [CONCEPT, "zero_concept"], [2016])
    assert [(r.concept_id, r.year, r.ads) for r in rows] == [
        (CONCEPT, 2016, 16406), ("zero_concept", 2016, 0)]
    assert all(r.source == "jobtech_historical" and r.fetched_at == T for r in rows)


def test_build_history_fails_on_a_missing_year(raw):
    with pytest.raises(FileNotFoundError, match=rf"{CONCEPT}.*2020"):
        jobsearch.build_history(raw, [CONCEPT], [2016, 2020, 2025])
