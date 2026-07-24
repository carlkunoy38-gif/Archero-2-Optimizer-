"""Exceptions raised by the repository layer.

These carry no HTTP semantics of their own — the API layer (`app/api/`)
is responsible for translating each one to a status code. Keeping them
plain Python exceptions means the repository functions stay usable from
non-HTTP callers (scripts, the future optimizer engine, tests) without
dragging in `fastapi.HTTPException`.
"""

from __future__ import annotations


class RepositoryError(Exception):
    """Base class for all repository-layer errors."""


class DuplicateDisplayNameError(RepositoryError):
    """Raised when creating an account whose display_name is already taken."""

    def __init__(self, display_name: str) -> None:
        self.display_name = display_name
        super().__init__(f"Display name {display_name!r} is already taken")


class ChapterNotFoundError(RepositoryError):
    """Raised when an account references a chapter id that doesn't exist."""

    def __init__(self, chapter_id: int) -> None:
        self.chapter_id = chapter_id
        super().__init__(f"Chapter {chapter_id} not found")
