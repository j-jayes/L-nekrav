"""REST adapter, version 1 (contracts/api-v1.md): validate, call core, return core models."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Request

from lonekrav.core.compare import CompareRequest, Comparison, compare
from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
from lonekrav.core.legal_flags import flags_for
from lonekrav.core.models import OccupationProfile
from lonekrav.core.salary import SalaryPayload, payload
from lonekrav.core.search import SearchAnswer, SearchRequest, run

router = APIRouter()


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
