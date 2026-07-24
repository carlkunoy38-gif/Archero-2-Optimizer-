"""Shared IntegrityError -> ConflictError translation.

Used by every service function that commits a write which *could*
violate a uniqueness constraint the caller can't fully rule out in
advance — either because two requests race each other (see
`equipment_service.py`'s equip/activate functions, where two concurrent
equips can both pass their own "clear the other one" step before
either commits — Module 1's partial unique indexes are what actually
stop the corrupted end state, not this code), or because of an
ordinary duplicate-creation request (`ownership_service.py`'s
`create_*` functions).
"""

from __future__ import annotations

from typing import NoReturn

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError


def raise_conflict_from_integrity_error(exc: IntegrityError, message: str) -> NoReturn:
    """Always raises: `ConflictError` if `exc` looks like a unique-constraint
    violation, otherwise `exc` itself, unmodified — so a genuinely
    unexpected integrity failure surfaces as a 500 (via the generic
    exception handler) rather than being mislabeled as a conflict."""

    orig_message = str(exc.orig)
    if "UNIQUE constraint failed" in orig_message or "unique constraint" in orig_message.lower():
        raise ConflictError(message) from exc
    raise exc
