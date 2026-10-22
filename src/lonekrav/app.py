"""The Lönekrav web app: one FastAPI app serving /api/v1 (Feature 003 mounts /mcp and /a2a here)."""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lonekrav.api import v1

log = logging.getLogger("lonekrav.access")


def create_app(engine=None, profiles=None, salaries=None) -> FastAPI:
    """`engine`, `profiles` and `salaries` (distributions, age bands) are injected by tests; the
    server loads the real ones at start-up."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from lonekrav.core.profiles import load_profiles
        from lonekrav.core.salary import load_age_bands, load_distributions
        from lonekrav.core.search import SearchEngine

        app.state.engine = engine or SearchEngine.load()
        app.state.profiles = profiles if profiles is not None else load_profiles()
        app.state.distributions, app.state.age_bands = salaries or (load_distributions(),
                                                                    load_age_bands())
        yield

    app = FastAPI(title="Lönekrav", version="1", lifespan=lifespan,
                  openapi_url="/api/v1/openapi.json", docs_url="/api/v1/docs", redoc_url=None)
    app.include_router(v1.router, prefix="/api/v1")

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        # Method, path, status and time only: request bodies are never logged (FR-033).
        start = time.perf_counter()
        response = await call_next(request)
        log.info("%s %s %s %.1fms", request.method, request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000)
        return response

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        log.error("%s %s failed: %s", request.method, request.url.path, type(exc).__name__)
        return JSONResponse({"detail": "internal error"}, status_code=500)

    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    uvicorn.run(create_app(), host="127.0.0.1", port=8000, access_log=False)
