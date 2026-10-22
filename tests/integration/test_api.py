"""The /api/v1 adapter over a fixture index (contracts/api-v1.md)."""

import logging


def add_route(app, path, endpoint):
    """Add a probe route ahead of the MCP root mount, which takes every path added after it."""
    app.add_api_route(path, endpoint, methods=["POST"])
    app.router.routes.insert(0, app.router.routes.pop())


def test_health(api_client):
    r = api_client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["index_chunks"] > 0 and "kblab" in body["models_loaded"]


def test_openapi_document_is_published(api_client):
    doc = api_client.get("/api/v1/openapi.json").json()
    assert doc["openapi"].startswith("3.") and "/api/v1/health" in doc["paths"]


def test_unexpected_error_hides_internals(api_client):
    def boom():
        raise RuntimeError("/Users/someone/secret/path.py exploded")

    add_route(api_client.app, "/api/v1/boom", boom)
    r = api_client.post("/api/v1/boom", json={"text": "x"})
    assert r.status_code == 500
    assert r.json() == {"detail": "internal error"}
    assert "secret" not in r.text


def test_request_bodies_are_not_logged(api_client, caplog):  # FR-033, research R7
    add_route(api_client.app, "/api/v1/echo", lambda: {"ok": True})
    with caplog.at_level(logging.DEBUG):
        api_client.post("/api/v1/echo", json={"text": "PRIVATE-AD-TEXT", "salary": 41234})
    assert "/api/v1/echo" in caplog.text  # the access line is there
    assert "PRIVATE-AD-TEXT" not in caplog.text and "41234" not in caplog.text


def test_serves_without_an_openrouter_key(fixture_engine, monkeypatch):  # FR-032
    from fastapi.testclient import TestClient

    from lonekrav.app import create_app

    monkeypatch.delenv("OPENROUTER_KEY", raising=False)
    engine, profiles = fixture_engine
    with TestClient(create_app(engine=engine, profiles=profiles)) as client:
        assert client.get("/api/v1/health").status_code == 200


OFFER = {"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100,
         "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}


def test_eligibility_returns_the_core_answer(api_client):
    from lonekrav.core.eligibility import EligibilityRequest, evaluate

    r = api_client.post("/api/v1/eligibility", json=OFFER)
    assert r.status_code == 200
    assert r.json() == evaluate(EligibilityRequest(**OFFER)).model_dump(mode="json")


def test_eligibility_invalid_body_names_the_field(api_client):
    r = api_client.post("/api/v1/eligibility", json=OFFER | {"fte_percent": 0})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][-1] == "fte_percent"


def test_eligibility_unknown_code_is_404(api_client):
    r = api_client.post("/api/v1/eligibility", json=OFFER | {"code": "1234"})
    assert r.status_code == 404 and "1234" in r.json()["detail"]


def test_search_route(api_client):
    r = api_client.post("/api/v1/search", json={"text": "mjukvaruutvecklare"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode_used"] == "fast" and body["hits"] and body["honest_fit"]


def test_search_rejects_oversized_text(api_client):
    r = api_client.post("/api/v1/search", json={"text": "x" * 20001})
    assert r.status_code == 422 and r.json()["detail"][0]["loc"][-1] == "text"


def test_salary_route(api_client):
    r = api_client.get("/api/v1/occupations/2512/salary",
                       params={"age_band": "25-34", "on": "2026-10-21"})
    assert r.status_code == 200
    body = r.json()
    assert body["title_en"] == "Software- and system developers"
    assert body["simulated"]["is_simulated"] is True
    assert any(d["year"] == 2025 and d["median"] == 53500 for d in body["distributions"])


def test_salary_route_errors(api_client):
    assert api_client.get("/api/v1/occupations/1234/salary").status_code == 404
    r = api_client.get("/api/v1/occupations/2512/salary", params={"age_band": "12-17"})
    assert r.status_code == 422 and "age_band" in r.text


def test_compare_route(api_client):
    r = api_client.post("/api/v1/compare", json={"codes": ["3511", "2512"],
                                                 "offer": OFFER | {"monthly_salary_sek": 32000}})
    assert r.status_code == 200
    body = r.json()
    assert [c["code"] for c in body["columns"]] == ["3511", "2512"]
    assert [c["eligibility"]["status"] for c in body["columns"]] == ["pass", "fail"]
    assert body["honest_fit"]


def test_compare_route_errors(api_client):
    r = api_client.post("/api/v1/compare", json={"codes": ["2512"]})
    assert r.status_code == 422 and "2–5" in r.text
    assert api_client.post("/api/v1/compare", json={"codes": ["2512", "1234"]}).status_code == 404


def test_occupation_route(api_client):
    r = api_client.get("/api/v1/occupations/3511")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "3511" and body["legal_flags"][0]["kind"] == "exempt_75"
    assert not any(d["source"]["source"] == "ilo_isco08" for d in body["descriptions"])
    assert api_client.get("/api/v1/occupations/1234").status_code == 404


def test_timeline_route(api_client):
    from lonekrav.core.legal import load_registry

    r = api_client.get("/api/v1/legal/timeline")
    assert r.status_code == 200
    events = r.json()
    assert len(events) == len(load_registry().timeline())
    assert all(e["source"]["url"] and e["source"]["checked_on"] for e in events)


def test_benchmark_route(api_client, tmp_path, monkeypatch):
    from lonekrav.api import v1

    monkeypatch.setattr(v1, "BENCHMARK_RESULTS", tmp_path / "missing.json")
    r = api_client.get("/api/v1/benchmark")
    assert r.status_code == 404 and "lonekrav-etl benchmark" in r.json()["detail"]
    (tmp_path / "missing.json").write_text('{"run_at": "x"}')
    assert api_client.get("/api/v1/benchmark").json() == {"run_at": "x"}


def test_parse_job_ad_route(api_client, fixtures):
    ad = (fixtures / "ads/en1_backend.txt").read_text()
    r = api_client.post("/api/v1/parse-job-ad", json={"text": ad})
    assert r.status_code == 200
    body = r.json()
    assert body["passages"][0] == {"index": 0, "text": "Backend Developer (Python)",
                                   "label": "title", "keep": True, "by": "position"}
    assert api_client.post("/api/v1/parse-job-ad", json={"text": ""}).status_code == 422


def test_compare_with_an_invalid_offer_is_422_not_500(api_client):  # Copilot review on PR #2
    offer = {k: v for k, v in OFFER.items() if k != "code"} | {"fte_percent": 0}
    r = api_client.post("/api/v1/compare", json={"codes": ["2512", "3511"], "offer": offer})
    assert r.status_code == 422 and "fte_percent" in r.text
