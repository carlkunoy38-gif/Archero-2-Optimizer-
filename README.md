# Archero 2 Optimizer

A companion planning tool for [Archero 2](https://www.habby.com/) players. It helps you
decide which hero, gear, and skills to invest in, which chapters are worth farming, and
what to upgrade next — based on data you enter about your own account.

**This project does not automate gameplay, read game memory, inject code into the game
client, or act as a bot.** It is a decision-support tool only: you tell it what you have,
it tells you what to do with it.

## Status

This repository is being built module by module. Completed so far:

- [x] **Module 1 — Foundation**: project scaffolding, environment configuration, logging,
      SQLAlchemy domain models for all Phase 1 entities, Alembic migrations, unit tests,
      CI (lint, type-check, test, migration round trip on every push).
- [x] **Module 2 — REST API**: FastAPI routers, Pydantic schemas, `GET /heroes`,
      `GET /weapons`, `GET /skills`, `POST /account`, under a versioned prefix
      (`/api/v1`), with OpenAPI docs at `/docs`.
- [ ] **Module 3** — Optimizer scoring engine (DPS / Survival / Boss / Farming / Overall
      scores) and the `/optimizer/build` and `/optimizer/upgrade` endpoints.
- [ ] **Module 4** — React + TypeScript + Tailwind frontend (Dashboard, My Account,
      Build Optimizer, Upgrade Advisor, Settings).
- [ ] **Module 5** — Real game data seeding (see "Game data" below).

## Project layout

```
backend/    FastAPI application, SQLAlchemy models, Alembic migrations
frontend/   React + TypeScript + Vite + Tailwind app (scaffolding lands in Module 4)
database/   SQLite database file lives here in development; seed data scripts
docs/       Architecture, installation, and development documentation
tests/      Backend test suite (pytest)
```

See [`docs/architecture.md`](docs/architecture.md) for the design of the layers above,
[`docs/installation.md`](docs/installation.md) to run it locally, and
[`docs/development.md`](docs/development.md) for day-to-day contributor workflow.

## Game data

Archero 2's real hero stats, weapon damage tables, rune effects, etc. are not available
to this project. Every catalog model is fully functional against **realistic placeholder
data** — the schema, relationships, and scoring math all work end-to-end — but the actual
numbers seeded into the database are illustrative, not datamined. Every file under
`backend/app/domain/models/` that contains placeholder values says so explicitly in its
module docstring. Real data can be added later purely as data (via `database/seeds/`),
with no schema changes required.

## License

Not yet decided — treat as all-rights-reserved until a license is added.
