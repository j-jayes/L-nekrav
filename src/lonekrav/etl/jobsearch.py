"""Yearly ad counts per JobTech occupation group from Arbetsförmedlingen's historical ads API.

One cached file per concept and year, so an interrupted fetch resumes; a year that was not
fetched fails the build rather than being stored as zero (Feature 005 FR-014, research R4).
Ads are CC0. Only counts are kept (limit=0): no ad text is downloaded.
"""

from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from lonekrav.core.models import YearlyAds
from lonekrav.etl.http import USER_AGENT, cached_get, read_meta

URL = "https://historical.api.jobtechdev.se/search"
FIRST_YEAR = 2016  # the interface has no coded ads before 2016
THREADS = 4


def years(today: dt.date) -> list[int]:
    """Full calendar years from 2016 to the last one before `today`."""
    return list(range(FIRST_YEAR, today.year))


def path_for(raw: Path, concept: str, year: int) -> Path:
    return raw / "jobsearch_history" / concept / f"{year}.json"


def _validate(data: bytes) -> None:
    int(json.loads(data)["total"]["value"])


def fetch_history(raw: Path, concepts: list[str], year_list: list[int],
                  force: bool = False) -> None:
    client = httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT})

    def one(job: tuple[str, int]) -> None:
        concept, year = job
        cached_get("jobsearch_history", URL, path_for(raw, concept, year), client=client,
                   force=force, validate=_validate,
                   params={"occupation-group": concept, "limit": "0",
                           "historical-from": f"{year}-01-01T00:00:00",
                           "historical-to": f"{year}-12-31T23:59:59"})

    jobs = [(c, y) for c in concepts for y in year_list]
    try:
        with ThreadPoolExecutor(THREADS) as pool:
            for i, _ in enumerate(pool.map(one, jobs), 1):
                if i % 500 == 0:
                    print(f"  jobsearch_history: {i}/{len(jobs)}", flush=True)
    finally:
        client.close()


def parse_year(path: Path) -> int:
    return int(json.loads(path.read_text())["total"]["value"])


def build_history(raw: Path, concepts: list[str], year_list: list[int]) -> list[YearlyAds]:
    rows = []
    for concept in concepts:
        for year in year_list:
            p = path_for(raw, concept, year)
            if not p.exists():
                raise FileNotFoundError(f"jobsearch_history: no count for {concept} in {year} "
                                        f"({p}); run lonekrav-etl fetch --only jobsearch_history")
            rows.append(YearlyAds(concept_id=concept, year=year, ads=parse_year(p),
                                  fetched_at=read_meta(p).fetched_at))
    return rows
