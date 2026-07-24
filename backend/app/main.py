"""FastAPI application factory and entry point.

Run with: ``uvicorn app.main:app --reload`` (from `backend/`).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_exception_handlers
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a fully configured FastAPI application.

    Accepting `settings` (rather than always calling `get_settings()`
    internally) is what makes this startup-safe to call more than once
    with different configuration — useful for tests that want a fresh
    app instance without mutating the process-wide cached `Settings`.
    """

    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Logged here (not at module import time) so importing app.main —
        # which every test does — doesn't emit a startup log line per
        # import; this only fires when something actually serves the app.
        logger.info(
            "%s starting up (environment=%s)", settings.app_name, settings.environment
        )
        yield
        logger.info("%s shutting down", settings.app_name)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
