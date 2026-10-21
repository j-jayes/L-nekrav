"""REST adapter, version 1 (contracts/api-v1.md): validate, call core, return core models."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from lonekrav.core.eligibility import EligibilityAnswer, EligibilityRequest, UnknownCode, evaluate
from lonekrav.core.search import SearchAnswer, SearchRequest, run

router = APIRouter()


def _known(request: Request) -> dict:
    return request.app.state.profiles


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
