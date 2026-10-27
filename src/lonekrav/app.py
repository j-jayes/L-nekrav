"""The Lönekrav web app: one FastAPI app serving /api/v1, /mcp, /a2a and the page at / (Feature 004)."""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastmcp.utilities.lifespan import combine_lifespans

from lonekrav.api import v1
from lonekrav.core.eligibility import UnknownCode
from lonekrav.protocols.a2a_server import add_a2a
from lonekrav.protocols.agent.loop import DEFAULT_MODEL, openrouter_model
from lonekrav.protocols.mcp_server import build_mcp

log = logging.getLogger("lonekrav.access")
# Libraries that log request or response bodies at DEBUG: tool arguments (fastmcp), JSON-RPC
# requests (a2a) and every streamed chunk (sse_starlette). They never go below INFO (FR-005).
CONTENT_LOGGERS = ("fastmcp", "a2a", "sse_starlette")
FRONTEND_DIST = Path("frontend/dist")  # `npm run build` in frontend/; the image copies it here


def create_app(engine=None, profiles=None, salaries=None, chat_model=None,
               frontend_dist: Path = FRONTEND_DIST, live=None, market=None) -> FastAPI:
    """`engine`, `profiles` and `salaries` (distributions, age bands) are injected by tests; the
    server loads the real ones at start-up. `chat_model` is the advisor's model; by default it is
    OpenRouter's when OPENROUTER_KEY is set, and None (the advisor declines) when it is not.
    `frontend_dist` is the built page, served at / when its index.html exists. `market` is
    (regional means, yearly ads), loaded from data/processed by default. `live` is the
    JobSearch cache (tests inject one that never touches the network); by default it calls
    LONEKRAV_JOBSEARCH_URL, or the real API."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from lonekrav.core.embeddings import SPECS
        from lonekrav.core.market import JOBSEARCH_URL, LiveCache, load_history
        from lonekrav.core.occupation_map import load_map, load_similarity
        from lonekrav.core.profiles import load_profiles
        from lonekrav.core.salary import load_age_bands, load_distributions, load_regional
        from lonekrav.core.search import SearchEngine
        from lonekrav.core.service import Service

        distributions, age_bands = salaries or (load_distributions(), load_age_bands())
        regional, history = market or (load_regional(), load_history())
        occupation_map = load_map()
        if occupation_map.model != SPECS["harrier"].identity:  # served, but marked (007 R5)
            logging.getLogger(__name__).warning("occupation map built with %s, index uses %s",
                                                occupation_map.model, SPECS["harrier"].identity)
            occupation_map = occupation_map.model_copy(update={"stale": True})
        app.state.service = Service(
            engine=engine or SearchEngine.load(),
            profiles=profiles if profiles is not None else load_profiles(),
            distributions=distributions, age_bands=age_bands, regional=regional,
            history=history, occupation_map=occupation_map, similarity=load_similarity(),
            live=live or LiveCache(base_url=os.environ.get("LONEKRAV_JOBSEARCH_URL")
                                   or JOBSEARCH_URL))
        yield

    for name in CONTENT_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(max(logging.INFO, logger.level))
    app = FastAPI(title="Lönekrav", version="1",
                  openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url=None)
    app.include_router(v1.router, prefix="/api/v1")
    app.state.mcp = build_mcp(app)
    if chat_model is None and (key := os.environ.get("OPENROUTER_KEY")):
        chat_model = openrouter_model(key, os.environ.get("LONEKRAV_LLM_MODEL") or DEFAULT_MODEL)
    add_a2a(app, app.state.mcp, chat_model)
    mcp_app = app.state.mcp.http_app(path="/mcp")  # mounted at "/" below: exactly /mcp (R2)
    app.router.lifespan_context = combine_lifespans(lifespan, mcp_app.lifespan)

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        # Method, path, status and time only: request bodies are never logged (FR-033).
        start = time.perf_counter()
        response = await call_next(request)
        log.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000)
        return response

    @app.exception_handler(UnknownCode)
    async def unknown_code(request: Request, exc: UnknownCode):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        log.error("%s %s failed: %s", request.method, request.url.path, type(exc).__name__)
        return JSONResponse({"detail": "internal error"}, status_code=500)

    _add_frontend(app, Path(frontend_dist))
    app.mount("/", mcp_app)  # last: a root mount takes every path registered after it
    return app


def _add_frontend(app: FastAPI, dist: Path) -> None:
    """The page keeps its state in the query string, so it needs only / and /assets: no catch-all
    route that would take /mcp from the root mount (research R2)."""
    index = dist / "index.html"
    if not index.is_file():
        @app.get("/", include_in_schema=False)
        def not_built():
            return JSONResponse({"detail": "frontend not built: run npm ci && npm run build in "
                                           "frontend/"}, status_code=404)
        return

    @app.get("/", include_in_schema=False)
    def page():
        return FileResponse(index)
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")


def main() -> None:
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()  # OPENROUTER_KEY and LONEKRAV_LLM_MODEL from .env; tests never read it

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    uvicorn.run(create_app(), host=os.environ.get("HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8000")), access_log=False)
