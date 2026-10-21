"""REST adapter, version 1 (contracts/api-v1.md): validate, call core, return core models."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from lonekrav.core.adparse import ParsedAd, parse
from lonekrav.core.compare import CompareRequest, Comparison, compare
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
from lonekrav.core.legal import TimelineEvent, load_registry
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import OccupationProfile
from lonekrav.core.salary import SalaryPayload, payload
from lonekrav.core.search import SearchAnswer, SearchRequest, run

router = APIRouter()
BENCHMARK_RESULTS = Path("data/processed/benchmark_results.json")


def _known(request: Request) -> dict:
    return request.app.state.profiles


def _profile(request: Request, code: str):
    if code not in request.app.state.profiles:
        raise HTTPException(404, f"unknown SSYK code {code!r}")
    return request.app.state.profiles[code]


@router.get("/health")
def health(request: Request) -> dict:
    engine = request.app.state.engine
    return {"status": "ok", "models_loaded": sorted(engine.embedders),
            "index_chunks": engine.store.count()}


@router.post("/eligibility")
def eligibility(body: EligibilityRequest, request: Request) -> EligibilityAnswer:
    try:
        return evaluate(body, known_codes=_known(request))
    except UnknownCode as e:
        raise HTTPException(404, str(e)) from e


@router.post("/search")
def search(body: SearchRequest, request: Request) -> SearchAnswer:
    return run(body, request.app.state.engine)


@router.get("/occupations/{code}/salary")
def salary(code: str, request: Request, age_band: str | None = None,
           on: dt.date | None = None) -> SalaryPayload:
    p = _profile(request, code)
    try:
        return payload(code, on=on or dt.date.today(), age_band=age_band,
                       distributions=request.app.state.distributions,
                       age_bands=request.app.state.age_bands,
                       titles={code: (p.title_sv, p.title_en)})
    except ValueError as e:  # an unknown age band
        raise HTTPException(422, str(e)) from e


@router.get("/occupations/{code}")
def occupation(code: str, request: Request) -> OccupationProfile:
    """The profile with registry legal flags; ILO text is never served (ILO reserves rights)."""
    p = _profile(request, code)
    return p.model_copy(update={
        "legal_flags": flags_for(code),
        "descriptions": [d for d in p.descriptions if d.source.source != "ilo_isco08"]})


@router.post("/compare")
def compare_codes(body: CompareRequest, request: Request) -> Comparison:
    for code in body.codes:
        _profile(request, code)
    return compare(body, profiles=request.app.state.profiles,
                   distributions=request.app.state.distributions,
                   age_bands=request.app.state.age_bands)


@router.get("/legal/timeline")
def timeline() -> list[TimelineEvent]:
    return load_registry().timeline()


@router.get("/benchmark")
def benchmark() -> dict:
    if not BENCHMARK_RESULTS.exists():
        raise HTTPException(404, "no benchmark results yet: run `lonekrav-etl benchmark`")
    return json.loads(BENCHMARK_RESULTS.read_text())


class AdText(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)


@router.post("/parse-job-ad")
def parse_job_ad(body: AdText, request: Request) -> ParsedAd:
    return parse(body.text, request.app.state.engine.embedders["kblab"])
