"""Call every /api/v1 route once against a running `lonekrav-serve` and print a markdown transcript.

    uv run lonekrav-serve &
    uv run python scripts/api_smoke.py > references/api-smoke.md

Offers are made up and job text is public example text (spec FR-033). Long lists in responses are
cut to their first three items for reading; the HTTP status and every other field are as returned.
"""

from __future__ import annotations

import datetime as dt
import json
import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OFFER = {"code": "2512", "monthly_salary_sek": 40000, "fte_percent": 100,
         "application_type": "first_permit", "filed_on": "2026-06-16", "decided_on": "2026-07-01"}
OLD_PERMIT = {"application_type": "extension", "current_permit_granted_on": "2026-01-10"}

CALLS = [
    ("Eligibility, scenario 1: 2512 filed 16 June 2026", "POST", "/eligibility", OFFER),
    ("Eligibility, scenario 2: filed 15 June 2026", "POST", "/eligibility",
     OFFER | {"filed_on": "2026-06-15"}),
    ("Eligibility, scenario 3: exempt code 3511", "POST", "/eligibility",
     OFFER | {"code": "3511", "filed_on": "2026-10-21", "decided_on": "2026-10-21"}),
    ("Eligibility, scenario 4: banned code 5343", "POST", "/eligibility", OFFER | {"code": "5343"}),
    ("Eligibility, scenario 5: 9210 partial ban", "POST", "/eligibility", OFFER | {"code": "9210"}),
    ("Eligibility, scenario 6: extension filed 30 Nov 2026, permit granted before June", "POST",
     "/eligibility", OFFER | OLD_PERMIT | {"filed_on": "2026-11-30", "decided_on": "2026-12-20"}),
    ("Eligibility, scenario 6: same extension filed 2 Dec 2026", "POST", "/eligibility",
     OFFER | OLD_PERMIT | {"filed_on": "2026-12-02", "decided_on": "2027-01-10"}),
    ("Eligibility, scenario 7: 80 % of full time", "POST", "/eligibility",
     OFFER | {"fte_percent": 80}),
    ("Eligibility, scenario 8: decided after June 2027 with no 2027 median", "POST",
     "/eligibility", OFFER | {"filed_on": "2027-06-20", "decided_on": "2027-06-20"}),
    ("Eligibility, scenario 9: declared young tech company", "POST", "/eligibility",
     OFFER | {"exemptions": ["young_tech_company"]}),
    ("Eligibility, scenario 10: 3511 on a transitional extension", "POST", "/eligibility",
     OFFER | OLD_PERMIT | {"code": "3511", "filed_on": "2026-11-30", "decided_on": "2026-12-20"}),
    ("Eligibility, scenario 11: filed 20 May 2026, decided 20 June", "POST", "/eligibility",
     OFFER | {"filed_on": "2026-05-20", "decided_on": "2026-06-20"}),
    ("Eligibility, scenario 12: extension of a permit granted 10 July 2026", "POST",
     "/eligibility", OFFER | OLD_PERMIT | {"current_permit_granted_on": "2026-07-10",
                                           "filed_on": "2026-11-30", "decided_on": "2026-12-20"}),
    ("Eligibility, out of scope: first permit decided 31 May 2026", "POST", "/eligibility",
     OFFER | {"filed_on": "2026-05-01", "decided_on": "2026-05-31"}),
    ("Eligibility, invalid: extension without a permit date", "POST", "/eligibility",
     OFFER | {"application_type": "extension"}),
    ("Eligibility, unknown code", "POST", "/eligibility", OFFER | {"code": "1234"}),
    ("Search, fast: backend developer", "POST", "/search", {"text": "backend developer"}),
    ("Search, full: backend developer", "POST", "/search",
     {"text": "backend developer", "mode": "full"}),
    ("Search, fast: sjuksköterska", "POST", "/search", {"text": "sjuksköterska"}),
    ("Search, title list", "POST", "/search",
     {"text": "Aktuarie/Försäkringsaktuarie/Försäkringsmatematiker", "mode": "full"}),
    ("Search, nonsense", "POST", "/search", {"text": "asdf"}),
    ("Health", "GET", "/health", None),
]


def trim(obj, n=3):
    if isinstance(obj, list):
        return [trim(x, n) for x in obj[:n]] + ([f"… {len(obj) - n} more"] if len(obj) > n else [])
    if isinstance(obj, dict):
        return {k: trim(v, n) for k, v in obj.items()}
    return obj


def main() -> None:
    print("# API smoke transcript\n")
    print(f"Run {dt.datetime.now().isoformat(timespec='seconds')} against `{BASE}` by "
          "`scripts/api_smoke.py`. Lists are cut to three items for reading.\n")
    with httpx.Client(base_url=BASE + "/api/v1", timeout=60) as c:
        for title, method, path, body in CALLS:
            r = c.request(method, path, json=body)
            print(f"## {title}\n\n`{method} /api/v1{path}` → **{r.status_code}**\n")
            if body is not None:
                print("```json\n" + json.dumps(body, ensure_ascii=False) + "\n```\n")
            print("```json\n" + json.dumps(trim(r.json()), ensure_ascii=False, indent=1) + "\n```\n")


if __name__ == "__main__":
    main()
