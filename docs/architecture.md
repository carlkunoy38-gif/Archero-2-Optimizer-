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
- Deleting a `UserAccount` cascades to delete its ownership rows without ever touching
  the shared catalog rows — verified in `tests/backend/test_models.py` and
  `tests/backend/test_constraints.py`.

`UserChapterProgress` follows the same pattern for chapter clear state (stars earned,
cleared flag), while `UserAccount.current_chapter` is a plain foreign key for "where is
this player right now," since that's a single value rather than a collection.

## Referential integrity

Every foreign key has an explicit `ondelete` rule instead of relying on the ORM alone
to keep things consistent — important because the ORM's own cascade bookkeeping never
runs for a bulk `DELETE` or a raw SQL statement, only for objects it loaded itself:

- `account_id` on every ownership/progress table: `ondelete="CASCADE"` — deleting an
  account takes its ownership rows with it, at the database level.
- `hero_id` / `weapon_id` / `armor_id` / `ring_id` / `amulet_id` / `pet_id` / `rune_id`
  / `skill_id` / `chapter_id`: `ondelete="RESTRICT"` — a catalog row that is currently
  owned by some account cannot be deleted out from under it.
- `UserAccount.current_chapter_id`: `ondelete="SET NULL"` — removing the chapter a
  player happens to be "currently on" from the catalog shouldn't take the account down
  with it.

On the ORM side, `UserAccount`'s collection relationships (`heroes`, `weapons`, ...)
combine `cascade="all, delete-orphan"` with `passive_deletes=True`: SQLAlchemy still
handles `delete-orphan` semantics (removing an item from `account.heroes` without
deleting the account), but when the *account itself* is deleted, SQLAlchemy no longer
loads and deletes each child row one at a time — it lets the database's
`ON DELETE CASCADE` do it.

**This only matters if the database actually enforces foreign keys.** SQLite does not,
by default, even when the schema declares them — an unrelated but critical fix, since
without it every `ondelete` rule above would be silently unenforced on SQLite (though
not on PostgreSQL, which enforces FKs unconditionally). `app.db.session.build_engine`
runs `PRAGMA foreign_keys=ON` on every SQLite connection it opens (`enable_sqlite_foreign_keys`),
and the test fixture (`tests/backend/conftest.py`) uses the same `build_engine` function
rather than a bare `create_engine`, specifically so tests exercise the same connection
behavior as the running application instead of a laxer one.

## Equipped-slot rules

Beyond "does this account own this item," several rows carry an `is_equipped` /
`is_active` / slot-index flag, and the schema enforces *how many can be true at once*
— deliberate Module 1 decisions, not left to the API layer, so they hold even against a
buggy or malicious direct-DB write:

| Table | Rule | Enforcement |
|---|---|---|
| `UserHeroOwnership` | at most one active hero per account | partial unique index on `account_id` where `is_active` |
| `UserWeaponOwnership` | at most one equipped weapon per account (single weapon slot) | partial unique index on `account_id` where `is_equipped` |
| `UserPetOwnership` | at most one active pet per account | partial unique index on `account_id` where `is_active` |
| `UserRingOwnership` | at most one equipped ring per account | partial unique index on `account_id` where `is_equipped` |
| `UserAmuletOwnership` | at most one equipped amulet per account | partial unique index on `account_id` where `is_equipped` |
| `UserArmorOwnership` | at most one equipped item per (account, slot) | partial unique index on `(account_id, slot)` where `is_equipped` |
| `UserRuneOwnership` | a socket index is used by at most one rune per account | plain `UniqueConstraint(account_id, socket_index)` |
| `UserSkillSelection` | an equip slot is used by at most one skill per account | plain `UniqueConstraint(account_id, equipped_slot)` |

The ring/amulet single-slot assumption is a placeholder pending confirmation of the
real slot counts, same as the illustrative stat values elsewhere.

Two things worth calling out:

- **Armor is the one case that needs a cross-table rule** — "one equipped item per
  slot" needs to know the `Armor` catalog row's `slot`, which lives on a different
  table than the uniqueness needs to be checked on. Rather than a trigger,
  `UserArmorOwnership.slot` denormalizes a copy of `armor.slot`, kept in sync by a
  `@validates("armor")` hook that fires the moment `.armor` is assigned (in Python,
  not deferred until flush) — see `app/domain/models/user_account.py`.
- **Runes and skills don't need partial indexes** because a plain `UniqueConstraint`
  already does the right thing: SQL treats `NULL` as distinct from every other `NULL`
  in a unique constraint, so "not socketed" / "not equipped" rows (`NULL` index) never
  collide with each other, only with another row that claims the *same* real index. A
  `CHECK` constraint on each table additionally keeps the boolean flag and the index
  column from disagreeing (`UserRuneOwnership`: `is_equipped` iff `socket_index` is
  set; `UserSkillSelection`: `equipped_slot` set implies `is_unlocked`).

*Maximum* socket/slot **counts** (how many runes can be socketed at once, how many
skill slots exist) are still unknown pending real game data and are left to the
service layer to validate in Module 2 — the schema only enforces "no two things in the
same slot," not "no more than N things equipped."

## Value constraints

Numeric columns that should never go negative (`gold`, `gems`, `energy`, `combat_power`
on `UserAccount`; `level`, `stars`, `star_level`, `attempts`, `stars_earned` on the
ownership/progress tables) have a `CheckConstraint` at the database level — Pydantic
validation in the API layer (Module 2) is the first line of defense, but the database
does not trust the application layer to be the only thing that ever writes to it.

## Naming convention and multi-column unique constraints

`Base.metadata`'s naming convention (`app/db/base.py`) uses
`"uq": "uq_%(table_name)s_%(column_0_N_name)s"` rather than the more common
`%(column_0_name)s` (first column only). Several ownership tables have two unique
constraints that share a leading column — e.g. `UserRuneOwnership` has both
`(account_id, rune_id)` and `(account_id, socket_index)` — and keying off only the
first column would generate the *identical* constraint name for both, which either
silently drops one constraint or fails outright depending on the backend.
`%(column_0_N_name)s` is a built-in SQLAlchemy naming-convention token that expands to
every column in the constraint, joined by underscores, avoiding the collision
entirely.

## Migrations

Alembic is wired to the app's own `Settings` (`app/core/config.py`) rather than a
hardcoded URL in `alembic.ini`, so migrations always run against the same database the
API server would use — switching `ARCHERO_DATABASE_URL` from SQLite to PostgreSQL
requires no changes to migration tooling. This is deliberate even though it means the
`sqlalchemy.url` set on an Alembic `Config` object passed in programmatically is
ignored (`alembic/env.py` always re-reads `get_settings().database_url`) — one place
decides the database URL, for the app and Alembic alike; see
`tests/backend/test_migrations.py` for how a test points this at a temp-file database
by setting the env var and clearing `get_settings`'s `lru_cache` instead of fighting
that design. `Base.metadata` uses an explicit naming convention for constraints/indexes
so Alembic's autogenerate produces stable, diffable migration scripts on both SQLite
and PostgreSQL.

## SQL logging

`Settings.sql_echo` (default `False`) is separate from `Settings.debug` on purpose:
`debug` toggles things like FastAPI's error pages, but echoing every SQL statement is
noisy and, in production, would end up logging user-entered values (item names,
display names) into general application logs. Turning on verbose SQL logging is an
explicit, separate opt-in (`ARCHERO_SQL_ECHO=true`), not a side effect of running in
debug mode.

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
