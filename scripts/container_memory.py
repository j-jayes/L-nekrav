"""Measure the container's memory under its compose cap while it serves each kind of request (R11).

    OPENROUTER_KEY= LONEKRAV_PORT=8001 docker compose up -d --force-recreate   # a fresh process
    uv run python scripts/container_memory.py http://127.0.0.1:8001 > references/container-memory.md

`docker stats` is sampled every second while the steps run in order. The full search loads the
accurate model (Harrier), which is the peak. If process memory does not fit under the cap (an OOM
kill, or more than 64 MiB in swap), stop and report to the maintainer before changing anything
(spec FR-027).
"""

from __future__ import annotations

import datetime as dt
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
AD = Path("tests/fixtures/ads/en1_backend.txt").read_text()
OFFER = {"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": "2026-10-01"}
STEPS = [
    ("idle after start-up", None),
    ("fast search, typed title", ("POST", "/api/v1/search", {"text": "backend developer"})),
    ("fast search, pasted ad", ("POST", "/api/v1/search", {"text": AD, "parse_ad": True})),
    ("full search, pasted ad (loads Harrier)",
     ("POST", "/api/v1/search", {"text": AD, "mode": "full", "parse_ad": True})),
    ("full search again", ("POST", "/api/v1/search", {"text": AD, "mode": "full", "parse_ad": True})),
    ("eligibility", ("POST", "/api/v1/eligibility", OFFER | {"code": "2512"})),
    ("compare three codes", ("POST", "/api/v1/compare", {"codes": ["2512", "2511", "3511"],
                                                         "offer": OFFER})),
]
UNITS = {"KiB": 2**10, "MiB": 2**20, "GiB": 2**30, "B": 1}


def to_bytes(s: str) -> float:
    for unit, n in UNITS.items():
        if s.endswith(unit):
            return float(s[: -len(unit)]) * n
    raise ValueError(s)


def main() -> None:
    cid = subprocess.run(["docker", "compose", "ps", "-q", "lonekrav"], capture_output=True,
                         text=True, check=True).stdout.strip()
    samples: list[tuple[float, float, float]] = []  # (time, used, limit)
    stop = threading.Event()

    def sample():
        while not stop.is_set():
            out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", cid],
                                 check=True, capture_output=True, text=True).stdout.strip()
            used, limit = (to_bytes(x.strip()) for x in out.split("/"))
            samples.append((time.monotonic(), used, limit))
            time.sleep(1)

    threading.Thread(target=sample, daemon=True).start()
    rows = []
    with httpx.Client(base_url=BASE, timeout=180) as c:
        for name, call in STEPS:
            t0 = time.monotonic()
            if call:
                method, path, body = call
                r = c.request(method, path, json=body)
                status = r.status_code
            else:
                status = "-"
            time.sleep(3)  # let the sampler see the step settle
            peak = max((u for t, u, _ in samples if t >= t0), default=0)
            rows.append((name, status, time.monotonic() - t0 - 3, peak))
    stop.set()
    limit = samples[-1][2]
    peak = max(u for _, u, _ in samples)
    gib = 2**30
    print(f"# Container memory\n\nRun {dt.datetime.now().isoformat(timespec='seconds')} against "
          f"`{BASE}` by `scripts/container_memory.py`, on a freshly started container (Apple M2 Pro, "
          f"Docker Desktop, linux/arm64). `docker stats` sampled every second.\n")
    print(f"**Peak {peak / gib:.2f} GiB of the {limit / gib:.2f} GiB limit "
          f"({100 * peak / limit:.0f} %).**\n")
    print("| Step | Status | Request time | Peak during step |\n|---|---|---|---|")
    for name, status, secs, p in rows:
        print(f"| {name} | {status} | {secs:.2f} s | {p / gib:.2f} GiB |")
    read = ("grep -E '^(anon|file) ' /sys/fs/cgroup/memory.stat; cat /sys/fs/cgroup/memory.peak"
            " /sys/fs/cgroup/memory.swap.current; grep -E '^(max|oom_kill) ' /sys/fs/cgroup/memory.events")
    v = subprocess.run(["docker", "exec", cid, "sh", "-c", read], check=True,
                       capture_output=True, text=True).stdout.split()
    anon, file, high, swap, max_events, oom_kills = (int(x) for x in (v[1], v[3], v[4], v[5], v[7], v[9]))
    mib = 2**20
    print(f"\nThe kernel's view at the end (cgroup v2): process (anon) memory {anon / gib:.2f} GiB, page "
          f"cache {file / gib:.2f} GiB, high-water mark {high / gib:.2f} GiB, swap in use "
          f"{swap / mib:.1f} MiB, OOM kills {oom_kills}. The limit was reached {max_events} times; "
          "the page cache (model and index files) fills up to the limit and is trimmed there, so "
          "these events alone are harmless.")
    if oom_kills or swap > 64 * mib:
        print("\nProcess memory does not fit under the cap: stop and report to the maintainer "
              "(FR-027).")


if __name__ == "__main__":
    main()
