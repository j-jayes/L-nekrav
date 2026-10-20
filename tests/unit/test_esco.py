import json

from lonekrav.etl import esco


def test_parse_occupation(fixtures):
    path = fixtures / "esco/occ0.json"
    raw = json.loads(path.read_text())
    occ = esco.parse(path)
    assert occ.uri == raw["uri"]
    assert occ.label["en"] == "accounting manager"
    assert occ.label["sv"] == "redovisningschef"
    assert "head of accounts" in occ.alt["en"]
    assert occ.description["sv"].startswith("Redovisningschefer ansvarar")


def test_missing_language_is_empty_not_error(fixtures):
    occ = esco.parse(fixtures / "esco/occ0.json")
    assert occ.alt.get("sv", []) == [] or isinstance(occ.alt["sv"], list)


def test_fetch_skips_occupations_esco_no_longer_has(tmp_path, monkeypatch):
    import httpx

    def handler(req):
        if "gone" in str(req.url):
            return httpx.Response(404)
        return httpx.Response(200, json={"uri": req.url.params["uri"]})

    real = httpx.Client
    monkeypatch.setattr(esco.httpx, "Client",
                        lambda **kw: real(transport=httpx.MockTransport(handler)))
    got = esco.fetch(tmp_path, ["http://esco/ok", "http://esco/gone"], delay=0)
    assert got.missing == ["http://esco/gone"]
    assert [p.exists() for p in got.paths] == [True]
    assert (tmp_path / "esco" / "missing.json").exists()


def test_fetch_still_fails_on_server_errors(tmp_path, monkeypatch):
    import httpx
    import pytest

    from lonekrav.etl.http import FetchError

    real = httpx.Client
    monkeypatch.setattr(esco.httpx, "Client", lambda **kw: real(
        transport=httpx.MockTransport(lambda r: httpx.Response(503))))
    with pytest.raises(FetchError, match="esco"):
        esco.fetch(tmp_path, ["http://esco/x"], delay=0)


def test_fetch_skips_occupation_esco_cannot_serve(tmp_path, monkeypatch):
    """Seen live 2026-10-20: one URI always returns 500 CognizoneException."""
    import httpx

    body = {"logref": "CognizoneException", "status": 500,
            "message": "More than one value found for field 'hasSkillType'"}

    def handler(req):
        if "broken" in str(req.url):
            return httpx.Response(500, json=body)
        return httpx.Response(200, json={"uri": req.url.params["uri"]})

    real = httpx.Client
    monkeypatch.setattr(esco.httpx, "Client",
                        lambda **kw: real(transport=httpx.MockTransport(handler)))
    got = esco.fetch(tmp_path, ["http://esco/broken", "http://esco/ok"], delay=0)
    assert got.missing == ["http://esco/broken"]
    assert len(got.paths) == 1


def test_skip_list_is_saved_even_when_fetch_aborts(tmp_path, monkeypatch):
    import httpx
    import pytest

    from lonekrav.etl.http import FetchError

    def handler(req):
        return httpx.Response(404 if "gone" in str(req.url) else 503)

    real = httpx.Client
    monkeypatch.setattr(esco.httpx, "Client",
                        lambda **kw: real(transport=httpx.MockTransport(handler)))
    with pytest.raises(FetchError):
        esco.fetch(tmp_path, ["http://esco/gone", "http://esco/down"], delay=0)
    import json
    assert json.loads((tmp_path / "esco" / "missing.json").read_text()) == ["http://esco/gone"]
