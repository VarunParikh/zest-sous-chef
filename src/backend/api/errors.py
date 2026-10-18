"""Error envelope and handlers (API Spec §5, §7). No stack traces or input values in responses."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.flows.templates import TEMPLATES
from backend.session.store import SessionBusy, SessionNotFound


class ApiError(Exception):
    def __init__(self, status: int, code: str, user_message: str, template_id: str | None = None,
                 retryable: bool = False, details: dict | None = None):
        super().__init__(code)
        self.status, self.code, self.user_message = status, code, user_message
        self.template_id, self.retryable, self.details = template_id, retryable, details or {}


def envelope(code: str, user_message: str, template_id: str | None = None, retryable: bool = False,
             details: dict[str, Any] | None = None) -> dict:
    return {"error": {"code": code, "template_id": template_id, "user_message": user_message,
                      "retryable": retryable, "details": details or {}}}


def internal_error(request_id: str) -> JSONResponse:
    return JSONResponse(status_code=500, content=envelope(
        "INTERNAL", TEMPLATES["MSG-SERVER"], "MSG-SERVER", retryable=True, details={"request_id": request_id}))


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status, content=envelope(
            exc.code, exc.user_message, exc.template_id, exc.retryable, exc.details))

    @app.exception_handler(SessionNotFound)
    async def _not_found(request: Request, exc: SessionNotFound):
        return JSONResponse(status_code=404, content=envelope(
            "SESSION_NOT_FOUND", "This chat session has ended. Starting a new one.", retryable=False))

    @app.exception_handler(SessionBusy)
    async def _busy(request: Request, exc: SessionBusy):
        return JSONResponse(status_code=409, content=envelope(
            "SESSION_BUSY", "Still working on your last message.", retryable=True))

    @app.exception_handler(RequestValidationError)
    async def _invalid(request: Request, exc: RequestValidationError):
        levers = request.method == "POST" and request.url.path == "/api/v1/sessions"
        # Only where and what failed; input values are never echoed back.
        errors = [{"loc": [str(p) for p in e.get("loc", ())], "msg": e.get("msg", "")} for e in exc.errors()]
        if levers:
            return JSONResponse(status_code=422, content=envelope(
                "INVALID_LEVERS", "Some lever values are out of range or not recognised.", details={"errors": errors}))
        return JSONResponse(status_code=422, content=envelope(
            "VALIDATION_ERROR", "That request was not valid.", details={"errors": errors}))
