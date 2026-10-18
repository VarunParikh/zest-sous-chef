"""FastAPI application (ADR-001; API Spec §2, §7)."""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from functools import lru_cache

from backend.api import errors
from backend.api.cart import router as cart_router
from backend.api.health import check_health, render_page
from backend.api.sessions import load_presets, router as sessions_router
from backend.catalogue.store import Store, load_store
from backend.config import Settings, load_settings
from backend.session.store import SessionStore
from backend.trace import Tracer

@lru_cache(maxsize=1)
def default_store() -> Store:
    return load_store()


LOCALHOST_ORIGINS = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"
log = logging.getLogger("zest")


def create_app(settings: Settings | None = None, http_transport: httpx.AsyncBaseTransport | None = None) -> FastAPI:
    settings = settings or load_settings()

    http = httpx.AsyncClient(transport=http_transport)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await http.aclose()

    app = FastAPI(title="Zest AI Sous-Chef (mock data)", version="0.0.1", lifespan=lifespan)
    app.state.settings = settings
    app.state.http = http
    app.state.tracer = Tracer(settings.resolve(settings.trace_path))
    app.state.presets = load_presets()
    app.state.store = default_store()  # the catalogue service; tests and stock scenarios swap it
    app.state.sessions = SessionStore(app.state.tracer, app.state.presets)

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        rid = uuid.uuid4().hex[:12]
        request.state.request_id = rid
        try:
            response = await call_next(request)
        except Exception:  # no stack traces or internals in responses (API Spec §7)
            log.exception("unhandled error, request_id=%s", rid)
            response = errors.internal_error(rid)
        response.headers["X-Request-Id"] = rid
        return response

    # Added after the request-id middleware so CORS headers also wrap error responses.
    app.add_middleware(CORSMiddleware, allow_origin_regex=LOCALHOST_ORIGINS, allow_methods=["*"], allow_headers=["*"])

    errors.install(app)
    app.include_router(sessions_router)
    app.include_router(cart_router)

    @app.get("/api/v1/health")
    async def health(request: Request) -> dict:
        return await check_health(request.app.state.settings, request.app.state.http)

    @app.get("/health", response_class=HTMLResponse)
    async def health_page(request: Request) -> str:
        return render_page(await check_health(request.app.state.settings, request.app.state.http))

    return app
