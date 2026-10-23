"""Check the running container on every surface and print a markdown transcript (Feature 004 T033).

    OPENROUTER_KEY= LONEKRAV_PORT=8001 docker compose up -d
    uv run python scripts/container_smoke.py http://127.0.0.1:8001 > references/container-smoke.md

It checks the page, REST, MCP and the agent card on one port; that no .env file or model key is
inside the container; and, with the container cut off from the network, that both searches still
work (the models and index are in the image). The ad is the public example en1_backend.txt.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SERVICE = "lonekrav"
AD = Path("tests/fixtures/ads/en1_backend.txt").read_text()
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()


def container() -> str:
    return sh("docker", "compose", "ps", "-q", SERVICE)


def mcp_tools(c: httpx.Client) -> list[str]:
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "smoke", "version": "0"}}}
    r = c.post("/mcp", json=init, headers=MCP_HEADERS)
    h = MCP_HEADERS | {"mcp-session-id": r.headers["mcp-session-id"]}
    c.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=h)
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers=h)
    data = next(json.loads(line[5:]) for line in r.text.splitlines() if line.startswith("data:"))
    return sorted(t["name"] for t in data["result"]["tools"])


def search(c: httpx.Client, mode: str) -> str:
    r = c.post("/api/v1/search", json={"text": AD, "mode": mode, "parse_ad": True}).json()
    return f"{r['mode_used']}: {[h['code'] for h in r['hits']]}"


def market(c: httpx.Client) -> str:
    m = c.get("/api/v1/occupations/2512/market").json()
    return (f"live {m['live']['status']} ({m['live']['ads']} ads), regional {m['regional_year']} "
            f"({len(m['regional'])} rows), history {m['history'][0]['year']}–{m['history'][-1]['year']}")


def main() -> None:
    run = dt.datetime.now().isoformat(timespec="seconds")
    out = [f"# Container smoke test\n\nRun {run} against `{BASE}` by `scripts/container_smoke.py`.\n"]

    def row(check: str, result: str) -> None:
        out.append(f"| {check} | {result} |")

    image = sh("docker", "image", "inspect", "lonekrav:latest", "--format", "{{.Size}}")
    out.append(f"Image `lonekrav:latest`: {int(image) / 1e9:.2f} GB.\n")
    out.append("| Check | Result |\n|---|---|")
    with httpx.Client(base_url=BASE, timeout=120) as c:
        page = c.get("/?view=search")
        row("`GET /` (the page)", f"{page.status_code} {page.headers['content-type']}, "
            f"title present: {'<title>Lönekrav</title>' in page.text}")
        row("`GET /api/v1/health`", c.get("/api/v1/health").text)
        card = c.get("/.well-known/agent-card.json").json()
        row("Agent card", f"{card['name']} at {card['supportedInterfaces'][0]['url']}")
        row("MCP `tools/list`", ", ".join(mcp_tools(c)))
        row("Fast search (en1 ad)", search(c, "fast"))
        row("Full search (en1 ad)", search(c, "full"))
        row("Market for 2512 (Feature 005)", market(c))
        cid = container()
        row("`.env` inside the container", sh("docker", "exec", cid, "sh", "-c",
                                               "ls -a /app | grep -c '^.env$' || true") + " files")
        key = sh("docker", "exec", cid, "printenv", "OPENROUTER_KEY")  # never printed, only tested
        row("`OPENROUTER_KEY` in the container", "set" if key else "not set")
        nets = sh("docker", "inspect", cid, "--format",
                  "{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}").split()
        for n in nets:
            sh("docker", "network", "disconnect", n, cid)
        try:
            offline = sh("docker", "exec", cid, "python", "-c", (
                "import json, urllib.request as u;"
                "req = lambda m: u.Request('http://127.0.0.1:8000/api/v1/search', method='POST',"
                f" data=json.dumps({{'text': {AD!r}, 'mode': m, 'parse_ad': True}}).encode(),"
                " headers={'Content-Type': 'application/json'});"
                "print([(m, json.load(u.urlopen(req(m)))['mode_used']) for m in ('fast', 'full')])"))
            row("Both searches with no network (from inside)", offline)
            live = sh("docker", "exec", cid, "python", "-c", (
                "import json, urllib.request as u, time; s = time.time();"
                "m = json.load(u.urlopen('http://127.0.0.1:8000/api/v1/occupations/2511/market'));"
                "print(m['live']['status'], m['live']['reason'], f'{time.time() - s:.1f} s')"))
            row("Market live count with no network (from inside)", live)
        finally:
            for n in nets:
                sh("docker", "network", "connect", n, cid)
    print("\n".join(out))


if __name__ == "__main__":
    main()
