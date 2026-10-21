"""REST adapter, version 1 (contracts/api-v1.md): validate, call core, return core models."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Request

from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
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
