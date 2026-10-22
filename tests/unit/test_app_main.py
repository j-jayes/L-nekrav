"""lonekrav-serve binds HOST and PORT from the environment (Feature 004 research R3)."""

import pytest


@pytest.fixture
def ran(monkeypatch):
    """Run main() with uvicorn.run and create_app stubbed; return uvicorn.run's kwargs."""
    import uvicorn

    from lonekrav import app

    seen = {}
    monkeypatch.setattr(uvicorn, "run", lambda _app, **kw: seen.update(kw))
    monkeypatch.setattr(app, "create_app", lambda: object())
    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)
    return lambda: (app.main(), seen)[1]


def test_defaults_to_localhost_8000(ran, monkeypatch):
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    assert (ran()["host"], ran()["port"]) == ("127.0.0.1", 8000)


def test_reads_host_and_port(ran, monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "8080")
    kw = ran()
    assert (kw["host"], kw["port"]) == ("0.0.0.0", 8080)
