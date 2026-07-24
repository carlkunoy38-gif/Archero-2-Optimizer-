# Development Guide

## Workflow

This project is built one module at a time rather than all at once — each module is
implemented, tested, and reviewed before the next one starts. See the root README's
"Status" section for what's landed and what's next.

## Adding or changing a domain model

1. Edit (or add) the model in `backend/app/domain/models/`.
2. If it's a new file, re-export the class from
   `backend/app/domain/models/__init__.py` (both the `import` line and `__all__`).
3. Generate a migration: `cd backend && alembic revision --autogenerate -m "..."`.
4. **Read the generated migration** — autogenerate does not detect every change
   (e.g. it won't infer a column rename, it'll see it as drop+add) — and adjust by
   hand if needed.
5. Apply it locally: `alembic upgrade head`.
6. Add/update tests in `tests/backend/test_models.py`.
7. Run `ruff check .`, `mypy app`, and `pytest ../tests/backend` before committing.

## Conventions

- **No bare strings for enumerable values.** If a field has a fixed set of valid
  values (rarity, hero class, stat type, ...), it's a `StrEnum` in
  `app/domain/models/enums.py`, not a raw `str` column.
- **Catalog vs. ownership.** Static game data goes on the catalog entity (`Hero`,
  `Weapon`, ...). Anything that varies per player (level, stars, equipped) goes on the
  matching `User<Entity>Ownership` table. See `docs/architecture.md`.
- **Settings, not hardcoded config.** Anything environment-specific (DB URL, log
  level, debug flag) goes through `app.core.config.Settings`, sourced from
  `ARCHERO_*` environment variables — never hardcode a connection string or path in
  application code.
- **Game data placeholders are explicit.** Any model or seed value that stands in for
  real Archero 2 data says so in a docstring headed `GAME DATA PLACEHOLDER`, so it's
  easy to grep for what needs replacing once real data is sourced.

## Testing philosophy

Model tests use an in-memory SQLite database (`tests/backend/conftest.py`) recreated
fresh per test — no shared test database, no ordering dependencies between tests.
Prefer testing behavior that would actually break silently (uniqueness constraints,
cascade behavior, relationship navigation in both directions) over trivial
attribute-assignment tests.

## Branching

All work for this project happens on `claude/archero2-optimizer-foundation-toa3l8`
until told otherwise.
