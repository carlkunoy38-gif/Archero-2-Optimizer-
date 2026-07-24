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
- [x] **Module 2 — REST API**: FastAPI routers/services/repositories, Pydantic schemas,
      paginated + filterable read endpoints for all nine catalog resources (heroes,
      weapons, armor, rings, amulets, pets, runes, skills, chapters), full account
      management (create/read/update, per-item ownership CRUD, chapter progress), and
      transactional equip/activate actions that auto-replace whatever was equipped
      before — all under a versioned prefix (`/api/v1`), with a consistent JSON error
      envelope and OpenAPI docs at `/docs`.
- [x] **Module 3 — Optimizer Engine**: a standalone, UI-independent decision engine
      (`app/optimizer/`) that aggregates an account's hero/gear/runes/pet/skills into a
      `BuildContext` and scores candidate options against it — never a static tier
      list. First advisor: the Skill Advisor (`POST /optimizer/skills/advise`), which
      ranks candidate in-run skill choices and explains why, using only the account's
      actual current build. Designed to carry future advisors (Gear, Farm, Upgrade,
      Rune, Resource) on the same engine.
- [x] **Module 3.1 — Effect-based marginal scoring**: skills now carry structured
      `SkillEffect` rows (projectile count, bounce count, attack speed, ...) instead of
      only a broad category, so two same-tier, same-category skills (Multishot vs.
      Ricochet vs. Attack Up) score differently. The advisor simulates adding each
      candidate to the build (`app.optimizer.simulator.apply_skill`) and measures the
      marginal gain against an `ObjectiveProfile` (balanced/boss/farm/survival) rather
      than a fixed formula — see "Module 3.1: effect-based marginal scoring" in
      `docs/architecture.md`.
- [x] **Module 4 — Frontend**: React + TypeScript + Vite + Tailwind app with routing for
      all five planned pages. **My Account** (create/switch accounts, manage every
      ownership type and chapter progress) and **Build Optimizer** (calls the Skill
      Advisor for a real recommendation) are fully functional against the live API —
      no mock data. **Dashboard**, **Upgrade Advisor**, and **Settings** are honest
      placeholders until their backend advisors/endpoints exist. See
      `frontend/README.md` and "Frontend architecture" in `docs/architecture.md`.
- [x] **Module 5 — Remaining Advisors**: Gear, Upgrade, and Chapter Advisors, built on
      the same Optimizer Engine as Skill Advisor — no new decision engine, no static
      tier lists. **Gear Advisor** (`POST /optimizer/gear/advise`) ranks an account's
      owned weapons/armor/rings/amulets/pets and recommends what to equip. **Upgrade
      Advisor** (`POST /optimizer/upgrade/advise`) finds the single best investment of
      an account's current gold across every ownable item, never recommending an
      upgrade that wouldn't actually improve the build. **Chapter Advisor** (`POST
      /optimizer/chapters/advise`) recommends the best chapter to farm or the best to
      push into next, and — when the account is under-powered for it — the best
      upgrade to make first, by reusing the Upgrade Advisor directly. See "Module 5:
      Gear, Upgrade, and Chapter Advisors" in `docs/architecture.md`.
- [ ] **Module 6** — Real game data seeding (see "Game data" below), and frontend pages
      for the three new advisors.

## Project layout

```
backend/    FastAPI application, SQLAlchemy models, Alembic migrations
frontend/   React + TypeScript + Vite + Tailwind app
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
