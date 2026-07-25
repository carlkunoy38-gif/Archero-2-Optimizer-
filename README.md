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
      placeholders until their backend advisors/endpoints exist (Upgrade Advisor's own
      page became functional in Module 6, below). See `frontend/README.md` and
      "Frontend architecture" in `docs/architecture.md`.
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
- [x] **Module 6 (partial) — Real rune data**: the first real (not placeholder) catalog
      data in this project, sourced from live-account screenshots — 10 real runes
      (Spin SPD Up, Sharp Arrow, Flamenox Seal, Vine Bind, Flamenox Touch, Circle,
      Frostshock Touch, Melee Sprite, Resilience, Intelligence) with real numeric
      effects, seeded via `database/seeds/seed_runes.py`. Real data revealed a real
      gap — the live game tracks per-summon-type damage (Circle/Sprite/Plant/Ice/
      Poison/Lightning/Fire) and a flat "ATK PWR" bonus that didn't exist as build
      dimensions yet — so `Rune` gained structured multi-effect rows (`RuneEffect`,
      mirroring how `SkillEffect` already works for skills) and `BuildContext` gained
      seven new fields, the same "extend, don't silently collapse" approach Module
      3.1 established. The seven new fields are now consumed too — `engine.summon_score`
      plus a new `ObjectiveProfile.summon_weight` mean a build's Circle/Sprite/Plant/
      Ice/Poison/Lightning/Fire investment actually affects every advisor's ranking,
      weighted highest under the `farm` objective. See "Module 6: real rune data..."
      in `docs/architecture.md`.
- [x] **Module 6 (partial) — Gear/Upgrade/Farm Advisor frontend pages**: three new
      functional pages calling the Module 5 endpoints — `GearAdvisorPage`,
      `UpgradeAdvisorPage` (replacing its placeholder), and `FarmAdvisorPage` (new nav
      item, for Chapter Advisor). Manual browser testing against a live backend caught
      a real bug the mocked-API unit tests missed: Upgrade Advisor's ranking spans
      every ownable category, and `catalog_id` is only unique *within* one category, so
      matching "recommended" by id alone double-badged a hero and a weapon that
      happened to share an id — fixed to match by ranking position instead, with a
      regression test locking it down. See "Gear, Upgrade, and Farm Advisor pages
      (Module 6)" in `docs/architecture.md`.
- [ ] **Module 6 (remaining)** — real data for the other eight catalog entities (see
      "Game data" below), and a combined Dashboard summarizing all advisors at once.

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

Archero 2's real hero stats, weapon damage tables, etc. mostly still aren't available to
this project. Runes are the first exception: `database/seeds/seed_runes.py` seeds 10 real
runes with real effect values, sourced from live-account screenshots (see "Module 6" in
`docs/architecture.md`). Every other catalog model (heroes, weapons, armor, rings,
amulets, pets, skills, chapters) is still fully functional against **realistic
placeholder data** — the schema, relationships, and scoring math all work end-to-end —
but the actual numbers seeded into the database for those entities remain illustrative,
not datamined. Every file under `backend/app/domain/models/` that contains placeholder
values says so explicitly in its module docstring.

Real data can usually be added later purely as data (via `database/seeds/`), but not
always with zero schema changes — seeding real rune data revealed the schema itself was
too simple (one rune granting several effects at once needed `RuneEffect` rows, not a
single scalar column), so "add real data" and "the schema might need to grow to hold it
honestly" should both be expected for the remaining catalog entities, not just the
former.

## License

Not yet decided — treat as all-rights-reserved until a license is added.
