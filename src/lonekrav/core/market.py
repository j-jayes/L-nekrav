"""Market pulse (Feature 005): live open ads per code, SCB's regional means and yearly ads.

Context only: none of it changes which code fits the duties or what the code requires. Live counts
come from Arbetsförmedlingen's JobSearch API when asked for and are reused for 15 minutes; a
failure is reported as unavailable, never as a number (FR-005). Regional means and yearly ads are
built by the ETL and passed in.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Literal
from urllib.parse import urlencode

import httpx
import polars as pl
from pydantic import BaseModel

from lonekrav.core.models import OccupationProfile, RegionalSalary, SourceRef, YearlyAds

JOBSEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
HISTORY = Path("data/processed/ad_history.parquet")
TTL = dt.timedelta(minutes=15)
TIMEOUT_S = 2.0  # per request; two requests per count keep a dead API under 5 s (SC-003)
USER_AGENT = "lonekrav/0.1 (+https://github.com/j-jayes/L-nekrav)"
MARKET_NOTICE = (
    "The SSYK code on a work-permit offer must match the duties actually performed. Open ads and "
    "regional pay are context: they are never a reason to choose a code. Regional figures are SCB "
    "means; the work-permit salary floor comes from the national median and is the same in every "
    "area.")

GetJson = Callable[[str, dict[str, str]], dict]  # (url, params) -> body; raises on failure


class CountyCount(BaseModel):
    name: str
    code: str
    ads: int


class LiveDemand(BaseModel):
    status: Literal["available", "no_concept", "unavailable"]
    concept_id: str | None = None
    ads: int | None = None
    positions: int | None = None
    counties: list[CountyCount] = []
    no_county: int | None = None
    reason: str | None = None
    fetched_at: dt.datetime | None = None
    source: SourceRef | None = None


class MarketAnswer(BaseModel):
    code: str
    title_sv: str
    title_en: str
    shared_with: list[str]
    live: LiveDemand
    regional_year: int | None
    regional: list[RegionalSalary]
    history_status: Literal["available", "no_concept"]
    history: list[YearlyAds]
    notice: str = MARKET_NOTICE


def write_history(rows: list[YearlyAds], path: Path = HISTORY) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump() for r in sorted(rows, key=lambda r: (r.concept_id, r.year))]
    pl.DataFrame(data, infer_schema_length=None).write_parquet(path, statistics=False)


def load_history(path: Path = HISTORY) -> list[YearlyAds]:
    return [YearlyAds.model_validate(r) for r in pl.read_parquet(path).to_dicts()]


def _params(concept: str, stats: bool) -> dict[str, str]:
    p = {"occupation-group": concept, "limit": "0"}
    return p | {"stats": "region", "stats.limit": "30"} if stats else p


def parse_live(concept: str, plain: dict, stats: dict, *, fetched_at: dt.datetime,
               url: str) -> LiveDemand:
    """`plain` gives ads and positions; `stats` gives the counties (it reports positions as 0).
    Raises ValueError for a body that is not a JobSearch answer."""
    try:
        values = next(s["values"] for s in stats["stats"] if s["type"] == "region")
        counties = sorted((CountyCount(name=v["term"], code=v["code"], ads=v["count"])
                           for v in values), key=lambda c: -c.ads)
        ads, positions = int(plain["total"]["value"]), int(plain["positions"])
        no_county = int(stats["total"]["value"]) - sum(c.ads for c in counties)
    except (KeyError, TypeError, StopIteration) as e:
        raise ValueError(f"unexpected JobSearch answer: {e!r}") from e
    query = f"{url}?{urlencode(_params(concept, stats=False))}"
    return LiveDemand(status="available", concept_id=concept, ads=ads, positions=positions,
                      counties=counties, no_county=max(no_county, 0), fetched_at=fetched_at,
                      source=SourceRef(source="jobtech_jobsearch",
                                       ref=f"occupation-group={concept}", url=query))


def _reason(e: Exception) -> str:
    if isinstance(e, httpx.TimeoutException):
        return "timeout"
    if isinstance(e, httpx.HTTPStatusError):
        return f"http {e.response.status_code}"
    if isinstance(e, httpx.TransportError):
        return "connection error"
    return "unexpected response"  # bad JSON, or a body parse_live rejects


class LiveCache:
    """Live counts per concept, reused for `ttl`. Only available answers are kept, so an API that
    recovers is seen on the next request. Fetches run outside the lock: two requests for the same
    concept at once may both fetch, which is harmless."""

    def __init__(self, get_json: GetJson | None = None, base_url: str = JOBSEARCH_URL,
                 clock: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.UTC),
                 ttl: dt.timedelta = TTL):
        self.get_json = get_json or _http_get_json()
        self.base_url, self.clock, self.ttl = base_url, clock, ttl
        self._kept: dict[str, LiveDemand] = {}
        self._lock = threading.Lock()

    def get(self, concept: str) -> LiveDemand:
        now = self.clock()
        with self._lock:
            kept = self._kept.get(concept)
        if kept and now - kept.fetched_at < self.ttl:
            return kept
        try:
            plain = self.get_json(self.base_url, _params(concept, stats=False))
            stats = self.get_json(self.base_url, _params(concept, stats=True))
            fresh = parse_live(concept, plain, stats, fetched_at=now, url=self.base_url)
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
            return LiveDemand(status="unavailable", concept_id=concept, reason=_reason(e))
        with self._lock:
            self._kept[concept] = fresh
        return fresh


def _http_get_json() -> GetJson:
    client = httpx.Client(timeout=TIMEOUT_S, headers={"User-Agent": USER_AGENT})

    def get_json(url: str, params: dict[str, str]) -> dict:
        r = client.get(url, params=params)
        r.raise_for_status()
        return r.json()
    return get_json


def market(profile: OccupationProfile, profiles: dict[str, OccupationProfile], live: LiveCache,
           regional: list[RegionalSalary], history: list[YearlyAds]) -> MarketAnswer:
    concept = profile.jobtech_concept_id
    shared = sorted(c for c, p in profiles.items()
                    if concept and p.jobtech_concept_id == concept and c != profile.code)
    rows = [r for r in regional if r.code == profile.code]
    year = max((r.year for r in rows), default=None)
    latest = sorted((r for r in rows if r.year == year),
                    key=lambda r: (r.region != "SE", r.region))  # Sweden first, then the areas
    return MarketAnswer(
        code=profile.code, title_sv=profile.title_sv, title_en=profile.title_en,
        shared_with=shared,
        live=live.get(concept) if concept else LiveDemand(status="no_concept"),
        regional_year=year, regional=latest,
        history_status="available" if concept else "no_concept",
        history=sorted((h for h in history if concept and h.concept_id == concept),
                       key=lambda h: h.year))
