"""Record real API responses for the page's unit tests (Feature 004 research R12).

    uv run lonekrav-serve &
    uv run python scripts/record_api_fixtures.py [BASE] [NAME ...]   # NAMEs: record only these

Writes one JSON file per call to frontend/src/test/fixtures/, so the page's tests run on what the
server actually returns (the 001 fixture rule: real slices, not hand-written data). Offers are made
up; the ad is the public example tests/fixtures/ads/en1_backend.txt. Each file is
{"status": ..., "body": ...}. Re-run after any change to a response model.

`market-unavailable` is recorded only when named, against a server whose JobSearch cannot be
reached: `LONEKRAV_JOBSEARCH_URL=http://127.0.0.1:9 uv run lonekrav-serve`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = Path(__file__).parents[1] / "frontend" / "src" / "test" / "fixtures"
AD = Path("tests/fixtures/ads/en1_backend.txt").read_text()
OFFER = {"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": "2026-10-01", "decided_on": "2026-10-22"}

CALLS = {
    "search-title-fast": ("POST", "/api/v1/search", {"text": "backend developer", "mode": "fast"}),
    "search-title-full": ("POST", "/api/v1/search", {"text": "backend developer", "mode": "full"}),
    "search-ad-fast": ("POST", "/api/v1/search", {"text": AD, "mode": "fast", "parse_ad": True}),
    "search-ad-full": ("POST", "/api/v1/search", {"text": AD, "mode": "full", "parse_ad": True}),
    "salary-2512": ("GET", "/api/v1/occupations/2512/salary?on=2026-10-22", None),
    "salary-2512-age": ("GET", "/api/v1/occupations/2512/salary?on=2026-10-22&age_band=25-34", None),
    "salary-2511": ("GET", "/api/v1/occupations/2511/salary?on=2026-10-22", None),
    "salary-3511-exempt": ("GET", "/api/v1/occupations/3511/salary?on=2026-10-22", None),
    "salary-5343-banned": ("GET", "/api/v1/occupations/5343/salary?on=2026-10-22", None),
    "salary-1211-suppressed": ("GET", "/api/v1/occupations/1211/salary?on=2026-10-22", None),
    "salary-1111-all-suppressed": ("GET", "/api/v1/occupations/1111/salary?on=2026-10-22", None),
    "salary-bad-age": ("GET", "/api/v1/occupations/2512/salary?age_band=99-100", None),
    "occupation-2512": ("GET", "/api/v1/occupations/2512", None),
    "occupation-9999": ("GET", "/api/v1/occupations/9999", None),
    "compare-2512-2511": ("POST", "/api/v1/compare", {"codes": ["2512", "2511"]}),
    "compare-offer": ("POST", "/api/v1/compare",
                      {"codes": ["2512", "2511", "3511"], "offer": OFFER | {"monthly_salary_sek": 30000}}),
    "eligibility-pass": ("POST", "/api/v1/eligibility", OFFER | {"code": "2512"}),
    "eligibility-part-time": ("POST", "/api/v1/eligibility",
                              OFFER | {"code": "2512", "fte_percent": 50, "monthly_salary_sek": 26000}),
    "eligibility-banned": ("POST", "/api/v1/eligibility", OFFER | {"code": "5343"}),
    "eligibility-invalid": ("POST", "/api/v1/eligibility",
                            OFFER | {"code": "2512", "filed_on": "2026-10-23"}),
    "timeline": ("GET", "/api/v1/legal/timeline", None),
    "registry": ("GET", "/api/v1/legal/registry", None),
    "agent-card": ("GET", "/.well-known/agent-card.json", None),
    "market-2512": ("GET", "/api/v1/occupations/2512/market", None),
    "market-1211": ("GET", "/api/v1/occupations/1211/market", None),
    "market-4430": ("GET", "/api/v1/occupations/4430/market", None),
    "market-unavailable": ("GET", "/api/v1/occupations/2512/market", None),
}
NAMED_ONLY = {"market-unavailable"}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE, timeout=120) as client:
        names = sys.argv[2:] or [n for n in CALLS if n not in NAMED_ONLY]
        for name in names:
            method, path, body = CALLS[name]
            r = client.request(method, path, json=body)
            (OUT / f"{name}.json").write_text(json.dumps(
                {"status": r.status_code, "body": r.json()}, indent=2, ensure_ascii=False) + "\n")
            print(f"{r.status_code} {method} {path} -> {name}.json")
