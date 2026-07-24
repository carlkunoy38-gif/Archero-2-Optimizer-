# Architecture Overview

## Layering

The backend follows a Clean Architecture split, enforced by import direction rather
than by framework magic:

```
app/
  core/     settings, logging — no dependency on anything else in the app
  db/       engine/session/declarative base — depends only on core
  domain/   ORM models (the entities) — depends only on db
  api/      FastAPI routers + Pydantic schemas (Module 2) — depends on domain
  services/ optimizer scoring engine (Module 3) — depends on domain, not on api
```

`domain/` never imports from `api/` or `services/`. This means the scoring engine and
the database models can be unit-tested and reused (e.g. from a CLI script) without
booting FastAPI, and the API layer is a thin adapter over the domain rather than the
place where business rules live.

## Catalog vs. account data

Ten entities were requested: Heroes, Weapons, Armor, Rings, Amulets, Pets, Runes,
Skills, Chapters, UserAccount. Nine of them (everything except `UserAccount`) are
**catalog data** — static facts about the game that are the same for every player
(a Legendary Bow has the same base damage for everyone). `UserAccount` is **player
data** — what a specific player currently owns and how far they've progressed it.

Rather than bolting player-specific columns (level, stars, equipped slot) onto the
shared catalog rows, each catalog entity has a matching `User<Entity>Ownership`
association table (e.g. `UserHeroOwnership`, `UserWeaponOwnership`) that links a
`UserAccount` to a catalog row and carries the player-specific state. This is the
standard SQLAlchemy "association object" pattern for many-to-many relationships that
need extra columns. Benefits:

- Catalog tables stay immutable reference data — safe to reseed/update without
  touching player state.
- A player's progress on an item is queried directly off their account
  (`account.heroes`, `account.weapons`, ...) without joining through the catalog.
- Deleting a `UserAccount` cascades to delete its ownership rows (`cascade="all,
  delete-orphan"` on the `UserAccount` side) without ever touching the shared catalog
  rows — verified in `tests/backend/test_models.py`.

`UserChapterProgress` follows the same pattern for chapter clear state (stars earned,
cleared flag), while `UserAccount.current_chapter` is a plain foreign key for "where is
this player right now," since that's a single value rather than a collection.

## Enumerations

Rarity, hero class, armor slot, and stat type are Python `enum.StrEnum` classes
(`app/domain/models/enums.py`), mapped to SQLAlchemy `Enum` columns. This means:

- Application code refers to `Rarity.LEGENDARY`, never the raw string `"legendary"` —
  a typo becomes an `AttributeError` at write-time instead of silently corrupting data.
- The database still stores a plain string column, so no custom type decoders are
  needed and the values are human-readable when inspecting the DB directly.

`StatType` exists as its own enum (rather than one column per possible stat on `Ring`/
`Amulet`/`Pet`/`Rune`) so a new stat can be introduced by adding an enum member, not by
running a schema migration.

## Migrations

Alembic is wired to the app's own `Settings` (`app/core/config.py`) rather than a
hardcoded URL in `alembic.ini`, so migrations always run against the same database the
API server would use — switching `ARCHERO_DATABASE_URL` from SQLite to PostgreSQL
requires no changes to migration tooling. `Base.metadata` uses an explicit naming
convention for constraints/indexes so Alembic's autogenerate produces stable,
diffable migration scripts on both SQLite and PostgreSQL.

## What's not decided yet

Modules 2–4 (API, scoring engine, frontend) will introduce their own design notes in
this file as they land. The scoring engine's weighting model in particular is meant to
be revisited once real game data is available — see the root README's "Game data"
section.
