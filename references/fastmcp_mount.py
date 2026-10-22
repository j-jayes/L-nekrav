"""FastMCP 4.1.3 mounted in FastAPI: a runnable reference.

    uv run python references/fastmcp_mount.py         # run every check (in-memory, TestClient, real uvicorn)
    uv run python references/fastmcp_mount.py serve   # just serve on 127.0.0.1:8765
"""

# A one-shot harness: it blocks while polling the server it starts, and prints any read error.
# ruff: noqa: ASYNC210, ASYNC220, ASYNC251, BLE001

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.utilities.lifespan import combine_lifespans
from pydantic import BaseModel

PORT = 8765


class LookupIn(BaseModel):
    code: str
    lang: str = "en"


class LookupOut(BaseModel):
    code: str
    title: str
    source: str
    thread: str  # which thread ran the tool (sync-tool check)
    via_request: str | None = None  # what get_http_request() exposed, if any


class Milestone(BaseModel):
    date: str
    event: str


def build_mcp(app: FastAPI) -> FastMCP:
    """Closure pattern: tools capture the parent FastAPI app and read app.state."""
    mcp = FastMCP("demo")

    @mcp.tool
    def lookup(query: LookupIn) -> LookupOut:  # sync on purpose
        thing = app.state.thing
        if query.code not in thing:
            raise ToolError(f"unknown SSYK code {query.code!r}")
        try:
            req = get_http_request()
            via = f"path={req.url.path} app={type(req.app).__name__} state.thing={'thing' in req.state._state}"
        except RuntimeError as exc:
            via = f"no request: {exc}"
        return LookupOut(
            code=query.code,
            title=thing[query.code],
            source="app.state.thing",
            thread=threading.current_thread().name,
            via_request=via,
        )

    @mcp.tool
    def boom(code: str) -> str:
        raise ValueError(f"plain exception for {code}")

    # GOTCHA (4.1.3): resources json.dumps() their return value. A BaseModel or a
    # list of BaseModels fails ("not JSON serializable" / "contents must be str...").
    # Dump to JSON-native data (or return a JSON str) yourself.
    @mcp.resource("legal://timeline", mime_type="application/json")
    def timeline() -> list[dict]:
        items = [
            Milestone(date="2026-06-16", event="floor 34 470 SEK"),
            Milestone(date="2027-06-01", event="next median"),
        ]
        return [m.model_dump(mode="json") for m in items]

    @mcp.resource("ssyk://{code}")
    def ssyk(code: str) -> dict:
        if code not in app.state.thing:
            raise ValueError(f"unknown code {code}")
        return {"code": code, "title": app.state.thing[code]}

    return mcp


def build_app() -> FastAPI:
    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        app.state.thing = {"2512": "Software developers", "1311": "IT managers"}
        print("[lifespan] app up", flush=True)
        yield
        print("[lifespan] app down", flush=True)

    # FastAPI needs the lifespan at construction, but the MCP app needs the
    # FastAPI app (closure). So: create app, then build mcp, then set lifespan.
    app = FastAPI()
    mcp = build_mcp(app)
    mcp_app = mcp.http_app(path="/mcp")  # route lives at /mcp inside the sub-app
    app.router.lifespan_context = combine_lifespans(app_lifespan, mcp_app.lifespan)

    @app.get("/api/v1/health")
    def health():
        return {"ok": True, "codes": sorted(app.state.thing)}

    app.mount("/", mcp_app)  # mount LAST, at root -> endpoint is exactly /mcp
    app.state.mcp = mcp
    return app


async def in_memory(app: FastAPI) -> None:
    print("\n=== in-memory Client(FastMCP) ===")
    # In-memory transport does not run the FastAPI lifespan: set state yourself.
    app.state.thing = {"2512": "Software developers"}
    async with Client(app.state.mcp) as c:
        tools = await c.list_tools()
        for t in tools:
            print("tool", t.name, "input", json.dumps(t.input_schema)[:160])
            print("     output", json.dumps(t.output_schema)[:200])
        r = await c.call_tool("lookup", {"query": {"code": "2512"}})
        print("structured_content:", r.structured_content)
        print("data:", type(r.data).__name__, r.data)
        print("is_error:", r.is_error)
        print("main thread:", threading.current_thread().name)

        try:
            await c.call_tool("lookup", {"query": {"code": "9999"}})
        except ToolError as exc:
            print("raise_on_error=True -> ToolError:", exc)
        r = await c.call_tool("lookup", {"query": {"code": "9999"}}, raise_on_error=False)
        print("ToolError raw: is_error", r.is_error, "content", r.content[0].text)
        r = await c.call_tool("boom", {"code": "x"}, raise_on_error=False)
        print("ValueError raw: is_error", r.is_error, "content", r.content[0].text)

        print("resources:", [str(x.uri) for x in await c.list_resources()])
        print("templates:", [x.uri_template for x in await c.list_resource_templates()])
        print("timeline:", (await c.read_resource("legal://timeline"))[0].text)
        print("ssyk://2512:", (await c.read_resource("ssyk://2512"))[0].text)
        try:
            await c.read_resource("ssyk://0000")
        except Exception as exc:
            print("bad template read ->", type(exc).__name__, exc)


def test_client_check() -> None:
    print("\n=== starlette TestClient ===")
    from starlette.testclient import TestClient

    app = build_app()
    with TestClient(app) as tc:  # `with` runs the combined lifespan
        print("GET /api/v1/health", tc.get("/api/v1/health").json())
        hdr = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
        init = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "t", "version": "0"}},
        }
        r = tc.post("/mcp", json=init, headers=hdr, follow_redirects=False)
        print("POST /mcp initialize ->", r.status_code, r.headers.get("mcp-session-id"), r.text[:120])
        r2 = tc.post("/mcp/", json=init, headers=hdr, follow_redirects=False)
        print("POST /mcp/ ->", r2.status_code)


async def over_http() -> None:
    print("\n=== uvicorn + Client('http://127.0.0.1:8765/mcp') ===")
    proc = subprocess.Popen([sys.executable, __file__, "serve"])
    try:
        for _ in range(100):
            try:
                httpx.get(f"http://127.0.0.1:{PORT}/api/v1/health", timeout=0.2)
                break
            except httpx.HTTPError:
                time.sleep(0.1)
        print("REST:", httpx.get(f"http://127.0.0.1:{PORT}/api/v1/health").json())
        async with Client(f"http://127.0.0.1:{PORT}/mcp") as c:
            r = await c.call_tool("lookup", {"query": {"code": "1311"}})
            print("HTTP data:", r.data)
            r = await c.call_tool("lookup", {"query": {"code": "nope"}}, raise_on_error=False)
            print("HTTP error: is_error", r.is_error, r.content[0].text)
        raw = httpx.post(f"http://127.0.0.1:{PORT}/mcp", json={}, follow_redirects=False)
        print("raw POST /mcp (no Accept) status:", raw.status_code, "(not 307)")
    finally:
        proc.terminate()
        proc.wait(5)
        print("server stopped, rc", proc.returncode)


if __name__ == "__main__":
    if sys.argv[1:] == ["serve"]:
        import uvicorn

        uvicorn.run(build_app(), host="127.0.0.1", port=PORT, log_level="warning")
    else:
        asyncio.run(in_memory(build_app()))
        test_client_check()
        asyncio.run(over_http())
