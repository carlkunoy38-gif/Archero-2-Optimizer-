"""Centralized logging configuration.

Every entry point (API server, CLI scripts, tests) should call
``configure_logging`` once at startup rather than calling
``logging.basicConfig`` ad hoc, so log formatting stays consistent across
the whole backend.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure the root logger according to application settings."""

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if configure_logging() is called more than
    # once (e.g. once by the ASGI server, once by a script importing app).
    if root.handlers:
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use."""

    configure_logging()
    return logging.getLogger(name)
