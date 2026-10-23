"""GET /api/v1/occupations/{code}/market (contracts/http.md): always 200 for a known code."""

import httpx
import pytest
from fastapi.testclient import TestClient

from lonekrav.app import create_app
from lonekrav.core.market import LiveCache


def client(fixture_engine, salaries, get_json):
    engine, profiles = fixture_engine
    app = create_app(engine=engine, profiles=profiles, salaries=salaries,
                     live=LiveCache(get_json=get_json))
    return TestClient(app, raise_server_exceptions=False)


def answers(url, params):
    if "stats" in params:
        return {"total": {"value": 5}, "stats": [{"type": "region", "values": [
            {"term": "Stockholms län", "code": "01", "count": 4}]}]}
    return {"total": {"value": 5}, "positions": 7}


def test_market_for_a_known_code(fixture_engine, salaries):
    with client(fixture_engine, salaries, answers) as c:
        r = c.get("/api/v1/occupations/2512/market")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "2512" and body["live"]["status"] == "available"
    assert (body["live"]["ads"], body["live"]["positions"], body["live"]["no_county"]) == (5, 7, 1)
    assert "must match the duties" in body["notice"]


def test_market_for_an_unknown_code_is_404(fixture_engine, salaries):
    with client(fixture_engine, salaries, answers) as c:
        r = c.get("/api/v1/occupations/9999/market")
    assert r.status_code == 404 and "9999" in r.json()["detail"]


@pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
def test_market_when_jobsearch_fails_is_still_200(fixture_engine, salaries, error):
    def broken(url, params):
        raise error

    with client(fixture_engine, salaries, broken) as c:
        r = c.get("/api/v1/occupations/2512/market")
    assert r.status_code == 200
    live = r.json()["live"]
    assert live["status"] == "unavailable" and live["ads"] is None and live["reason"]
