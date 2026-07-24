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
6. Add/update tests — model shape and relationships go in
   `tests/backend/test_models.py`; FK/CHECK/uniqueness rules go in
   `tests/backend/test_constraints.py`.
7. Run `ruff check .`, `mypy app`, and `pytest ../tests/backend` before committing.

## Adding an API endpoint

1. Add/extend a Pydantic schema in `backend/app/schemas/` for the request and/or
   response shape. Mirror any DB-level `CheckConstraint` with a matching Pydantic
   `Field` constraint (e.g. `ge=0`) so bad input gets a 422 without a DB round trip.
2. Add the data-access function to the matching `backend/app/repositories/` module.
   Anything that's a real persistence invariant (uniqueness, a required reference)
   belongs here as a typed exception from `app/repositories/errors.py` — repositories
   never raise `HTTPException` or import anything from `fastapi`.
3. Add the router in `backend/app/api/v1/`, and register it in
   `backend/app/api/v1/router.py`. Catch each repository exception you expect and map
   it to a status code; let anything else propagate (FastAPI turns it into a 500)
   rather than mislabeling an unexpected failure.
4. Add tests in `tests/backend/test_api_<resource>.py` using the `client` fixture
   (`tests/backend/conftest.py`) — cover the success path, validation failures (422),
   and every repository-error -> status-code mapping the router added.
5. Run `ruff check .`, `mypy app`, and `pytest ../tests/backend` before committing.

## Conventions

- **No bare strings for enumerable values.** If a field has a fixed set of valid
  values (rarity, hero class, stat type, ...), it's a `StrEnum` in
  `app/domain/models/enums.py`, not a raw `str` column.
- **Catalog vs. ownership.** Static game data goes on the catalog entity (`Hero`,
  `Weapon`, ...). Anything that varies per player (level, stars, equipped) goes on the
  matching `User<Entity>Ownership` table. See `docs/architecture.md`.
- **The database enforces its own invariants — it does not trust the API layer.**
  A value that should never be negative gets a `CheckConstraint`, not just a Pydantic
  validator in Module 2. A row that should be unique per account (an equipped slot, a
  socket index) gets a real unique constraint or partial unique index. See
  "Equipped-slot rules" and "Value constraints" in `docs/architecture.md` before adding
  a new `is_equipped`/`is_active`/slot-index style column — decide and enforce the
  cardinality rule in the same change that adds the column.
- **Every foreign key states its `ondelete` rule explicitly** — `CASCADE` for
  `account_id` (deleting an account takes its data with it), `RESTRICT` for a
  reference to catalog data (can't delete a `Hero` that's currently owned), `SET NULL`
  for an optional "currently pointing at" reference. Don't leave `ondelete` unset and
  rely on the ORM's Python-side cascade — that only runs for objects the ORM itself
  loaded, never for a bulk delete or raw SQL.
- **Settings, not hardcoded config.** Anything environment-specific (DB URL, log
  level, debug flag, SQL echo) goes through `app.core.config.Settings`, sourced from
  `ARCHERO_*` environment variables — never hardcode a connection string or path in
  application code.
- **Game data placeholders are explicit.** Any model or seed value that stands in for
  real Archero 2 data says so in a docstring headed `GAME DATA PLACEHOLDER`, so it's
  easy to grep for what needs replacing once real data is sourced.
- **Repositories are data access, not business logic.** A repository function may
  enforce a genuine persistence invariant (a required reference exists, a value is
  unique) but shouldn't grow multi-entity decision logic — that's what `services/` is
  for (reserved for the Module 3 optimizer engine). See "API layer" in
  `docs/architecture.md` for the reasoning.
- **New endpoints are versioned.** Every route except `GET /health` is mounted under
  `Settings.api_v1_prefix` (`app/main.py`) — don't add a bare top-level path.

## Testing philosophy

Model tests use an in-memory SQLite database (`tests/backend/conftest.py`) recreated
fresh per test via `app.db.session.build_engine` — the same connection setup
(including `PRAGMA foreign_keys=ON`) the running application uses, not a bare
`create_engine`, so tests exercise real behavior rather than a laxer stand-in. No
shared test database, no ordering dependencies between tests.

Prefer testing behavior that would actually break silently over trivial
attribute-assignment tests: uniqueness constraints, `ondelete` cascade/restrict/set-null
behavior (ideally via a raw core `delete()`/`insert()` that bypasses the ORM's own
cascade logic, so the test proves the *database* enforces it), relationship navigation
in both directions, and CHECK-constraint edge cases. `tests/backend/test_migrations.py`
additionally runs the real Alembic upgrade/downgrade chain against a temp-file
database — don't assume `Base.metadata.create_all()` (used by the in-memory fixture)
and the actual migration scripts stay in sync; test both.

## Branching

All work for this project happens on `claude/archero2-optimizer-foundation-toa3l8`
until told otherwise.
