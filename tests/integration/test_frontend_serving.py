"""The page is served at / and /assets, next to the MCP root mount (Feature 004 research R2)."""

import pytest
from fastapi.testclient import TestClient

INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}}


@pytest.fixture
def serve(fixture_engine, salaries):
    """A TestClient for an app serving the page from `dist` (None: no build)."""
    from lonekrav.app import create_app

    engine, profiles = fixture_engine
    clients = []

    def make(dist):
        client = TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries,
                                       frontend_dist=dist), raise_server_exceptions=False)
        clients.append(client.__enter__())
        return client
    yield make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Lönekrav</title>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    return tmp_path


def mcp_answers(client):
    r = client.post("/mcp", json=INIT, follow_redirects=False,
                    headers={"Accept": "application/json, text/event-stream"})
    return r.status_code == 200 and bool(r.headers.get("mcp-session-id"))


def test_serves_the_index_with_any_query(serve, dist):
    client = serve(dist)
    for path in ("/", "/?view=compare&codes=2512,2514"):
        r = client.get(path)
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
        assert "<title>Lönekrav</title>" in r.text


def test_serves_assets_and_404s_unknown_ones(serve, dist):
    client = serve(dist)
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/assets/nope.js").status_code == 404


def test_without_a_build_says_how_to_build(serve, tmp_path):
    r = serve(tmp_path / "missing").get("/")
    assert r.status_code == 404 and "frontend not built" in r.json()["detail"]


@pytest.mark.parametrize("built", [True, False])
def test_other_surfaces_unchanged(serve, dist, tmp_path, built):
    client = serve(dist if built else tmp_path / "missing")
    assert mcp_answers(client)
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/.well-known/agent-card.json").json()["name"] == "lonekrav-advisor"
