"""The MCP adapter over a fixture index (contracts/mcp.md): same answers as /api/v1."""

import asyncio

import pytest

TOOLS = {"search_occupations", "extract_job_ad_signal", "get_occupation_salary",
         "evaluate_permit_eligibility", "compare_occupations"}


def mcp_call(api_client, fn):
    """Run `fn(client)` against the app's MCP server over the in-memory transport."""
    from fastmcp import Client

    async def go():
        async with Client(api_client.app.state.mcp) as c:
            return await fn(c)
    return asyncio.run(go())


def tool(api_client, name, args):
    return mcp_call(api_client, lambda c: c.call_tool(name, args, raise_on_error=False))


def test_lists_exactly_the_five_tools(api_client):
    tools = mcp_call(api_client, lambda c: c.list_tools())
    assert {t.name for t in tools} == TOOLS
    for t in tools:
        assert t.description and t.input_schema["properties"] and t.output_schema


def test_lists_the_two_resources(api_client):
    async def both(c):
        return await c.list_resources(), await c.list_resource_templates()

    resources, templates = mcp_call(api_client, both)
    assert [str(r.uri) for r in resources] == ["legal://timeline"]
    assert [t.uri_template for t in templates] == ["ssyk://{code}"]


OFFER = {"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100,
         "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
NO_CODE = {k: v for k, v in OFFER.items() if k != "code"}


def same_as_rest(api_client, name, args, method, path, **rest):
    r = tool(api_client, name, args)
    assert not r.is_error, r.content
    expected = getattr(api_client, method)(path, **rest)
    assert expected.status_code == 200
    assert r.structured_content == expected.json()


@pytest.mark.parametrize("body", [{"text": "mjukvaruutvecklare"},
                                  {"text": "Backend developer building Python APIs", "k": 3}])
def test_search_equals_rest(api_client, body):
    same_as_rest(api_client, "search_occupations", {"request": body}, "post", "/api/v1/search",
                 json=body)


def test_search_with_parse_ad_equals_rest(api_client, fixtures):
    body = {"text": (fixtures / "ads/en1_backend.txt").read_text(), "parse_ad": True}
    same_as_rest(api_client, "search_occupations", {"request": body}, "post", "/api/v1/search",
                 json=body)


def test_extract_job_ad_signal_equals_rest(api_client, fixtures):
    body = {"text": (fixtures / "ads/en1_backend.txt").read_text()}
    same_as_rest(api_client, "extract_job_ad_signal", {"request": body}, "post",
                 "/api/v1/parse-job-ad", json=body)


@pytest.mark.parametrize("params", [{}, {"age_band": "25-34", "on": "2026-10-21"}])
def test_salary_equals_rest(api_client, params):
    same_as_rest(api_client, "get_occupation_salary", {"code": "2512", **params}, "get",
                 "/api/v1/occupations/2512/salary", params=params)


def test_eligibility_equals_rest(api_client):
    same_as_rest(api_client, "evaluate_permit_eligibility", {"request": OFFER}, "post",
                 "/api/v1/eligibility", json=OFFER)


@pytest.mark.parametrize("body", [{"codes": ["2512", "2421"]},
                                  {"codes": ["3511", "2512"], "offer": NO_CODE}])
def test_compare_equals_rest(api_client, body):
    same_as_rest(api_client, "compare_occupations", {"request": body}, "post", "/api/v1/compare",
                 json=body)


def read(api_client, uri):
    import json

    contents = mcp_call(api_client, lambda c: c.read_resource(uri))
    return json.loads(contents[0].text)


def test_timeline_resource_equals_rest(api_client):
    assert read(api_client, "legal://timeline") == api_client.get("/api/v1/legal/timeline").json()


def test_ssyk_resource_equals_rest(api_client):
    assert read(api_client, "ssyk://3511") == api_client.get("/api/v1/occupations/3511").json()


@pytest.mark.parametrize(("name", "args", "path", "method", "rest"), [
    ("get_occupation_salary", {"code": "1234"}, "/api/v1/occupations/1234/salary", "get", {}),
    ("evaluate_permit_eligibility", {"request": OFFER | {"code": "1234"}}, "/api/v1/eligibility",
     "post", {"json": OFFER | {"code": "1234"}}),
    ("compare_occupations", {"request": {"codes": ["2512", "1234"]}}, "/api/v1/compare", "post",
     {"json": {"codes": ["2512", "1234"]}}),
    ("get_occupation_salary", {"code": "2512", "age_band": "12-17"},
     "/api/v1/occupations/2512/salary", "get", {"params": {"age_band": "12-17"}}),
])
def test_expected_errors_carry_rests_text(api_client, name, args, path, method, rest):
    r = tool(api_client, name, args)
    expected = getattr(api_client, method)(path, **rest)
    assert expected.status_code in (404, 422)
    assert r.is_error and r.content[0].text == expected.json()["detail"]


def test_unknown_profile_resource(api_client):
    from mcp.shared.exceptions import MCPError

    with pytest.raises(MCPError, match="unknown SSYK code '1234'"):
        read(api_client, "ssyk://1234")


@pytest.mark.parametrize(("args", "field"), [
    ({"request": {"text": "x" * 20001}}, "text"),
    ({"request": {"text": "developer", "k": 21}}, "k"),
])
def test_invalid_arguments_name_the_field(api_client, args, field):
    r = tool(api_client, "search_occupations", args)
    assert r.is_error and field in r.content[0].text


def test_unexpected_errors_are_masked(api_client, monkeypatch):
    from lonekrav.core.service import Service

    def boom(self, req):
        raise RuntimeError("/Users/someone/secret/path.py exploded")

    monkeypatch.setattr(Service, "search", boom)
    r = tool(api_client, "search_occupations", {"request": {"text": "developer"}})
    assert r.is_error and "secret" not in r.content[0].text
    monkeypatch.undo()
    assert not tool(api_client, "search_occupations", {"request": {"text": "developer"}}).is_error


def test_tool_arguments_are_not_logged(fixture_engine, salaries, caplog, monkeypatch):  # FR-005
    import logging

    from fastapi.testclient import TestClient

    from lonekrav.app import create_app

    # fastmcp logs each tool's arguments at DEBUG, through its own stderr handlers. Turn it to
    # DEBUG as FASTMCP_LOG_LEVEL=DEBUG would, and send its records to caplog too.
    fm = logging.getLogger("fastmcp")
    monkeypatch.setattr(fm, "propagate", True)
    level = fm.level
    fm.setLevel(logging.DEBUG)
    try:
        engine, profiles = fixture_engine
        with TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries)) as c, \
                caplog.at_level(logging.DEBUG):
            tool(c, "search_occupations", {"request": {"text": "PRIVATE-AD-TEXT"}})
            tool(c, "evaluate_permit_eligibility",
                 {"request": OFFER | {"monthly_salary_sek": 41234}})
            tool(c, "evaluate_permit_eligibility",
                 {"request": OFFER | {"monthly_salary_sek": 41234, "code": "1234"}})
    finally:
        fm.setLevel(level)
    assert "PRIVATE-AD-TEXT" not in caplog.text and "41234" not in caplog.text


def test_served_at_exactly_slash_mcp_beside_rest(api_client):  # research R2
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"}}}
    r = api_client.post("/mcp", json=init, follow_redirects=False,
                        headers={"Accept": "application/json, text/event-stream"})
    assert r.status_code == 200 and r.headers.get("mcp-session-id")
    assert api_client.get("/api/v1/health").status_code == 200
