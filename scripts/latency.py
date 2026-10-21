"""Search latency against a running `lonekrav-serve` (spec SC-003, research R2/R3).

    uv run lonekrav-serve &
    uv run python scripts/latency.py > references/search-latency.md

Fast: 200 single-title queries (benchmark titles, both languages). Full: 50 queries, half titles
and half long texts of about 600 words (official occupation descriptions joined, searched as they
are). Ads: the ten made-up ads in tests/fixtures/ads, five times each, in full mode with
`parse_ad`, the way a pasted ad is meant to be searched (research R3). Times are client-side round trips over HTTP on localhost, after one warm-up request per
mode (the first full request loads Harrier).
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def titles(n: int) -> list[str]:
    qs = json.loads(Path("data/processed/benchmark_generated.json").read_text())
    out = [t for q in qs for t in (q["text_sv"], q.get("text_en")) if t and "/" not in t]
    return out[:n]


def long_texts(n: int, words: int = 600) -> list[str]:
    profiles = json.loads(Path("data/processed/ssyk_profiles.json").read_text())
    texts, buf = [], []
    for p in profiles:  # a list of profile records
        buf += [d["text"] for d in p["descriptions"] if d["lang"] == "en"]
        if sum(len(t.split()) for t in buf) >= words:
            texts.append(" ".join(" ".join(buf).split()[:words]))
            buf = []
        if len(texts) == n:
            return texts
    return texts


def measure(client: httpx.Client, texts: list[str], mode: str,
            parse_ad: bool = False) -> list[float]:
    body = {"mode": mode, "parse_ad": parse_ad}
    client.post("/search", json={"text": texts[0], **body}).raise_for_status()  # warm-up
    ms = []
    for t in texts:
        start = time.perf_counter()
        r = client.post("/search", json={"text": t, **body})
        ms.append((time.perf_counter() - start) * 1000)
        r.raise_for_status()
        assert r.json()["mode_used"] == mode, r.json().get("fallback_reason")
    return ms


def row(name: str, ms: list[float], budget: float) -> str:
    p95 = statistics.quantiles(ms, n=20)[-1]
    return (f"| {name} | {len(ms)} | {statistics.median(ms):.1f} | {p95:.1f} | {max(ms):.1f} | "
            f"{budget:.0f} | {'pass' if p95 < budget else 'FAIL'} |")


def main() -> None:
    fast_q = titles(200)
    full_q = titles(25) + long_texts(25)
    with httpx.Client(base_url=BASE + "/api/v1", timeout=60) as c:
        fast = measure(c, fast_q, "fast")
        full = measure(c, full_q, "full")
        ads = measure(c, [p.read_text() for p in sorted(Path("tests/fixtures/ads").glob("*.txt"))]
                      * 5, "full", parse_ad=True)
    print("# Search latency\n")
    print(f"Run {time.strftime('%Y-%m-%d %H:%M')} on {platform.machine()} {platform.system()} "
          "by `scripts/latency.py` (client-side round trips, models warm).\n")
    print("| Mode | n | median ms | p95 ms | max ms | budget ms | |\n|---|---|---|---|---|---|---|")
    print(row("fast (titles)", fast, 50))
    print(row("full (all)", full, 1000))
    print(row("full: titles", full[:25], 1000))
    print(row("full: ~600-word texts", full[25:], 1000))
    print(row("full + parse_ad: pasted ads", ads, 1000))


if __name__ == "__main__":
    main()
