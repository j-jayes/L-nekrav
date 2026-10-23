"""One real JobSearch call through the market route (Feature 005 FR-007). Skipped offline.

    uv run pytest -m live -k market
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from lonekrav.core.market import JOBSEARCH_URL


def _online() -> bool:
    try:
        return httpx.get(JOBSEARCH_URL, params={"limit": "0"}, timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.live  # the probe runs in the test, so collection stays offline (FR-007)


def test_live_count_matches_jobsearch(fixture_engine, salaries):
    from lonekrav.app import create_app

    if not _online():
        pytest.skip("JobSearch unreachable")
    engine, profiles = fixture_engine
    concept = profiles["2512"].jobtech_concept_id
    with TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries)) as c:
        live = c.get("/api/v1/occupations/2512/market").json()["live"]
    direct = httpx.get(JOBSEARCH_URL, params={"occupation-group": concept, "limit": "0"},
                       timeout=5).json()
    assert live["status"] == "available"
    assert abs(live["ads"] - direct["total"]["value"]) <= 0.02 * direct["total"]["value"]
    assert live["positions"] >= live["ads"] > 0  # an ad offers one position or more
    assert sum(c["ads"] for c in live["counties"]) + live["no_county"] <= live["ads"] * 1.02
