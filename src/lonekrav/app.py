"""The Lönekrav web app: one FastAPI app serving /api/v1 (Feature 003 mounts /mcp and /a2a here)."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastmcp.utilities.lifespan import combine_lifespans

from lonekrav.api import v1
from lonekrav.core.eligibility import UnknownCode
from lonekrav.protocols.mcp_server import build_mcp

log = logging.getLogger("lonekrav.access")


def create_app(engine=None, profiles=None, salaries=None) -> FastAPI:
    """`engine`, `profiles` and `salaries` (distributions, age bands) are injected by tests; the
    server loads the real ones at start-up."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from lonekrav.core.profiles import load_profiles
        from lonekrav.core.salary import load_age_bands, load_distributions
        from lonekrav.core.search import SearchEngine
        from lonekrav.core.service import Service

        distributions, age_bands = salaries or (load_distributions(), load_age_bands())
        app.state.service = Service(
            engine=engine or SearchEngine.load(),
            profiles=profiles if profiles is not None else load_profiles(),
            distributions=distributions, age_bands=age_bands)
        yield

    app = FastAPI(title="Lönekrav", version="1",
                  openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url=None)
    app.include_router(v1.router, prefix="/api/v1")
    app.state.mcp = build_mcp(app)
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

    app.mount("/", mcp_app)  # last: a root mount takes every path registered after it
    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    uvicorn.run(create_app(), host="127.0.0.1", port=8000, access_log=False)
