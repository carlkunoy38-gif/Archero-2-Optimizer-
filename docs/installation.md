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

Interactive OpenAPI docs (Swagger UI) are then available at `http://localhost:8000/docs`
(ReDoc at `/redoc`, raw schema at `/openapi.json`). Every endpoint is mounted under
`/api/v1` except `GET /health`, e.g. `http://localhost:8000/api/v1/heroes` — see
`docs/architecture.md` ("API layer") for why. The nine catalog list endpoints will
return an empty array until you seed catalog data (see `database/seeds/`) or insert
rows some other way — the schema doesn't ship with sample rows.

**`ARCHERO_DEBUG` defaults to `true`**, which is what you want locally (FastAPI/
Starlette's own debug tooling). **Any deployment reachable by someone other than you
must set `ARCHERO_DEBUG=false`** — with debug mode on, an unhandled exception returns
Starlette's own HTML/text traceback instead of this project's error envelope,
potentially exposing internals. See "Consistent error envelope" in
`docs/architecture.md`.

### Endpoint groups

| Prefix | What it is |
|---|---|
| `GET /heroes`, `/weapons`, `/armor`, `/rings`, `/amulets`, `/pets`, `/runes`, `/skills`, `/chapters` (+ `/{id}`) | Read-only catalog data, paginated (`limit`/`offset`) and filterable (e.g. `?rarity=epic`) |
| `POST /accounts`, `GET /accounts/{id}`, `PATCH /accounts/{id}` | Account creation, full detail (with every owned item and chapter progress), and resource/current-chapter updates |
| `POST/PATCH/DELETE /accounts/{id}/<heroes\|weapons\|armor\|rings\|amulets\|pets\|runes\|skills>` | Own, update the progression of, or drop an item; `PUT /accounts/{id}/chapters/{id}/progress` upserts chapter progress |
| `POST /accounts/{id}/<...>/{item_id}/<activate\|deactivate\|equip\|unequip>` | Transactional equip/activate actions — see `docs/architecture.md` ("Equip actions") |
| `POST /optimizer/skills/advise` | Skill Advisor (Module 3) — ranks candidate in-run skill choices against one account's actual current build; never a static tier list. See `docs/architecture.md` ("The Optimizer Engine") |

Full request/response shapes are in Swagger UI at `/docs` — this table is a map, not a
reference.

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

Requires the backend already running (see above) — the frontend has no data of its own.

```bash
cd frontend
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if the backend isn't on the default port
npm run dev
```

Open `http://localhost:5173`. The backend's default CORS configuration
(`Settings.cors_allow_origins`) already allows this origin.

### Verify

```bash
npm run lint       # oxlint
npm run typecheck   # tsc -b --noEmit
npm run test        # vitest run
npm run build       # type-check + production build
```

### What's actually functional

**My Account**, **Build Optimizer**, **Gear Advisor**, **Upgrade Advisor**, and **Farm
Advisor** all call the real API — create/switch an account, manage every ownership
type, and get real Skill/Gear/Upgrade/Chapter Advisor recommendations. **Dashboard**
and **Settings** are placeholders that explain why they're not built yet — a combined
account-score summary and a weights read/write endpoint, respectively — rather than
showing fake data. See "Frontend architecture" in `docs/architecture.md`.
