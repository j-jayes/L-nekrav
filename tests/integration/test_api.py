"""The /api/v1 adapter over a fixture index (contracts/api-v1.md)."""

import logging


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

    api_client.app.add_api_route("/api/v1/boom", boom, methods=["POST"])
    r = api_client.post("/api/v1/boom", json={"text": "x"})
    assert r.status_code == 500
    assert r.json() == {"detail": "internal error"}
    assert "secret" not in r.text


def test_request_bodies_are_not_logged(api_client, caplog):  # FR-033, research R7
    api_client.app.add_api_route("/api/v1/echo", lambda: {"ok": True}, methods=["POST"])
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
