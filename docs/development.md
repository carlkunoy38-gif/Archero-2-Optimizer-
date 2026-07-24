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

Four layers, always in this order — see "API layer" in `docs/architecture.md` for the
full reasoning:

1. **Schema** (`backend/app/schemas/`): the request/response shape. Mirror any DB-level
   `CheckConstraint` with a matching Pydantic `Field` constraint (e.g. `ge=0`) so bad
   input gets a 422 without a DB round trip. If a field must never be client-settable
   (armor's `slot`; any `is_equipped`/`is_active`/socket-or-slot-index field), leave it
   off the `Create`/`Update` schema entirely — that's the actual enforcement, not a
   comment saying not to accept it.
2. **Repository** (`backend/app/repositories/`): pure data access — get, list, add,
   delete. No decisions here: a "get" that finds nothing returns `None`, it does not
   raise. If several equip actions need the same shape of "clear this flag on every
   other row," that's a shared repository helper (see `ownership.py::clear_other_equipped`);
   a decision like "does clearing apply account-wide or scoped to one slot" is the
   caller's (the service's) job to specify via extra `WHERE` clauses, not the
   repository's to decide.
3. **Service** (`backend/app/services/`): every decision — does the referenced
   account/catalog item exist (`NotFoundError` if not), is this a duplicate
   (`ConflictError` if so), does an equip action need to replace something first. Raise
   `app.core.exceptions.NotFoundError` / `ConflictError` — never `fastapi.HTTPException`
   — so this layer stays callable from a script or the optimizer engine without a
   FastAPI dependency.
4. **Route** (`backend/app/api/routes/`, registered in `backend/app/api/router.py`):
   call exactly one service function and set the success status code (201 create, 200
   read/update, 204 delete). Don't catch exceptions here — `app/api/error_handlers.py`
   already translates every `NotFoundError`/`ConflictError`/validation failure into the
   standard error envelope; a route-level `try`/`except` would just be redundant.

Then: add tests in `tests/backend/test_api_<resource>.py` using the `client` fixture
(`tests/backend/conftest.py`) — success path, validation failures (422), and every
`NotFoundError`/`ConflictError` the service can raise, mapped to the right status code.
Run `ruff check .`, `mypy app`, and `pytest ../tests/backend` before committing.

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
- **Repositories are data access, not business logic.** A repository function never
  decides anything — no "if missing, raise," no uniqueness pre-checks, no HTTP-shaped
  exceptions. That's what `services/` is for, and it's also where the Module 3
  optimizer engine will live. See "API layer" in `docs/architecture.md` for the
  reasoning.
- **New endpoints are versioned.** Every route except `GET /health` is mounted under
  `Settings.api_v1_prefix` (`app/main.py`) — don't add a bare top-level path.
- **Errors are domain exceptions, not `HTTPException`.** Services raise
  `app.core.exceptions.NotFoundError` / `ConflictError`; routes never construct an
  error response by hand. If a genuinely new *kind* of error condition comes up that
  doesn't fit either, add a new `AppError` subclass and a handler for it in
  `app/api/error_handlers.py` rather than reaching for `HTTPException` in a route.
- **`ARCHERO_DEBUG=false` in any real deployment.** Debug mode makes Starlette render
  its own traceback page for an unhandled exception instead of the custom error
  envelope — see "Consistent error envelope" in `docs/architecture.md`. This is not
  optional for anything actually exposed to users.

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
