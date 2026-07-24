"""Exception handlers so every error response shares one JSON shape.

Whatever goes wrong — a domain error raised deliberately, a Pydantic
validation failure, an unmatched route, or a genuinely unexpected bug —
the client always gets back::

    {"error": {"type": "...", "message": "...", "details": ...}}

``details`` is only present where there's structured information worth
returning (currently: field-level validation errors). This means a
client never has to special-case "is this FastAPI's default error body
or ours" — there is only ours.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int, error_type: str, message: str, *, details: Any = None
) -> JSONResponse:
    body: dict[str, Any] = {"error": {"type": error_type, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up every handler below on `app`. Call once, from `create_app`."""

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, "not_found", exc.message)

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return _error_response(status.HTTP_409_CONFLICT, "conflict", exc.message)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        # Fallback for any AppError subclass added later without its own
        # handler above — still a "your request was invalid" response,
        # not a 500.
        return _error_response(status.HTTP_400_BAD_REQUEST, "invalid_request", exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Request validation failed",
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Anything reaching here is a bug, not a client mistake: log the
        # real exception server-side, but never let its details (e.g. raw
        # SQL from an IntegrityError) reach the response body.
        logger.exception("Unhandled exception processing %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "Internal server error"
        )
