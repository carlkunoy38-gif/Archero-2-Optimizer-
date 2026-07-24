"""Domain-level exceptions raised by services (and, for a plain "not
found", repositories returning `None`).

These carry no HTTP semantics of their own — `app/api/error_handlers.py`
is what translates each one into a status code and a response body.
Keeping them plain Python exceptions with no FastAPI import means
services and repositories stay usable from a script or the future
optimizer engine without a FastAPI dependency.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all domain-level errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """A referenced resource (account, catalog item, ownership row, ...) does
    not exist."""


class ConflictError(AppError):
    """The request conflicts with the current state: a duplicate, a slot
    that's already taken, or a business rule that blocks the requested
    state transition (e.g. equipping a skill that isn't unlocked yet)."""
