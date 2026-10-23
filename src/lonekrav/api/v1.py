"""REST adapter, version 1 (contracts/api-v1.md): validate, call core, return core models."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from lonekrav.core.adparse import AdText, ParsedAd
from lonekrav.core.compare import CompareRequest, Comparison
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest
from lonekrav.core.legal import Registry, TimelineEvent
from lonekrav.core.market import MarketAnswer
from lonekrav.core.models import OccupationProfile
from lonekrav.core.salary import SalaryPayload
from lonekrav.core.search import SearchAnswer, SearchRequest
from lonekrav.core.service import Service

router = APIRouter()
BENCHMARK_RESULTS = Path("data/processed/benchmark_results.json")


def _service(request: Request) -> Service:
    return request.app.state.service


@router.get("/health")
def health(request: Request) -> dict:
    engine = _service(request).engine
    return {"status": "ok", "models_loaded": sorted(engine.embedders),
            "index_chunks": engine.store.count()}


@router.post("/eligibility")
def eligibility(body: EligibilityRequest, request: Request) -> EligibilityAnswer:
    return _service(request).eligibility(body)


@router.post("/search")
def search(body: SearchRequest, request: Request) -> SearchAnswer:
    return _service(request).search(body)


@router.get("/occupations/{code}/salary")
def salary(code: str, request: Request, age_band: str | None = None,
           on: dt.date | None = None) -> SalaryPayload:
    try:
        return _service(request).salary(code, on=on, age_band=age_band)
    except ValueError as e:  # an unknown age band
        raise HTTPException(422, str(e)) from e


@router.get("/occupations/{code}/market")
def market(code: str, request: Request) -> MarketAnswer:
    return _service(request).market(code)


@router.get("/occupations/{code}")
def occupation(code: str, request: Request) -> OccupationProfile:
    return _service(request).occupation(code)


@router.post("/compare")
def compare_codes(body: CompareRequest, request: Request) -> Comparison:
    return _service(request).compare(body)


@router.get("/legal/timeline")
def timeline(request: Request) -> list[TimelineEvent]:
    return _service(request).timeline()


@router.get("/legal/registry")
def registry(request: Request) -> Registry:
    """Every rule, median, code list, exemption and statement, with sources: the legal guide's data."""
    return _service(request).registry()


@router.get("/benchmark")
def benchmark() -> dict:
    if not BENCHMARK_RESULTS.exists():
        raise HTTPException(404, "no benchmark results yet: run `lonekrav-etl benchmark`")
    return json.loads(BENCHMARK_RESULTS.read_text())


@router.post("/parse-job-ad")
def parse_job_ad(body: AdText, request: Request) -> ParsedAd:
    return _service(request).parse_ad(body)
