"""CLI entry point for seeding the Rune catalog.

The actual seed data and logic live in `app.seeds.runes` (part of the
`app` package, so it's covered by the project's normal ruff/mypy/pytest
setup) — this script is just a thin, directly-runnable wrapper. Run it
from `backend/` so the `app` package resolves:

    cd backend
    python ../database/seeds/seed_runes.py
"""

from __future__ import annotations

from app.db.session import SessionLocal
from app.seeds.runes import seed_runes


def main() -> None:
    with SessionLocal() as db:
        inserted = seed_runes(db)
    print(f"Seeded {inserted} rune(s).")


if __name__ == "__main__":
    main()
