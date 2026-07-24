# Installation Guide

## Prerequisites

- Python 3.12+
- Node.js 20+ (for the frontend, arriving in Module 4)

## Backend setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev,postgres]"

cp .env.example .env               # adjust ARCHERO_* values if needed
```

The `postgres` extra (the `psycopg` driver) is only required to actually *connect* to
PostgreSQL, but the test suite also exercises that dialect's code path
(`tests/backend/test_settings.py`), so install it even if you plan to stick with the
SQLite default — otherwise one test fails with `ModuleNotFoundError: psycopg` for
reasons that have nothing to do with your change. CI installs both extras for the
same reason.

### Initialize the database

The default configuration uses SQLite at `database/archero2.db` (relative to the repo
root, regardless of which directory you run commands from). Apply migrations:

```bash
alembic upgrade head
```

This creates every Phase 1 table (heroes, weapons, armor, rings, amulets, pets, runes,
skills, chapters, user accounts, and their ownership tables).

### Run the test suite

```bash
pytest ../tests/backend -v
```

### Lint and type-check

```bash
ruff check .
mypy app
```

### Run the API server

```bash
uvicorn app.main:app --reload
```

Interactive OpenAPI docs are then available at `http://localhost:8000/docs` (and the
raw schema at `/openapi.json`). Every endpoint is mounted under `/api/v1` except
`GET /health`, e.g. `http://localhost:8000/api/v1/heroes` — see
`docs/architecture.md` ("API layer") for why. Note that `GET /heroes`, `/weapons`, and
`/skills` will return an empty list until you seed catalog data (see `database/seeds/`)
or insert rows some other way — the schema doesn't ship with sample rows.

## Switching to PostgreSQL

Install the optional `postgres` extra (adds the `psycopg` driver):

```bash
pip install -e ".[postgres]"
```

Set `ARCHERO_DATABASE_URL` in `.env` to a PostgreSQL DSN, e.g.:

```
ARCHERO_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/archero2
```

Then run `alembic upgrade head` again — no application code changes are required.
Note: the SQLite-only integrity fixes documented in `docs/architecture.md`
("Referential integrity") — enabling `PRAGMA foreign_keys` — are no-ops on PostgreSQL,
which enforces foreign keys unconditionally, so behavior is consistent either way.

## Frontend setup

Not yet scaffolded — see `frontend/README.md` for status. Instructions will be added
here in Module 4.
