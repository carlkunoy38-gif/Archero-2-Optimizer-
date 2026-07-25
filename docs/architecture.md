# Architecture Overview

## Layering

The backend follows a Clean Architecture split, enforced by import direction rather
than by framework magic:

```
app/
  core/          settings, logging, exceptions — no dependency on anything else in the app
  db/            engine/session/declarative base — depends only on core
  domain/        ORM models (the entities) — depends only on db
  repositories/  data access functions over a Session — depends only on domain
  schemas/       Pydantic request/response models — depends only on domain (for
                 enums) and Pydantic itself, never on repositories/services/api
  services/      business logic — depends on repositories, schemas, core.exceptions;
                 never on FastAPI or the api/ layer
  optimizer/     decision/recommendation engine (Module 3) — depends only on domain
                 (see "The Optimizer Engine (Module 3)" below for why this is its own
                 top-level package rather than living under services/)
  seeds/         one-off real-game-data catalog seeding logic (Module 6) — depends
                 only on domain; run via database/seeds/*.py CLI wrappers, never by
                 the running API itself
  api/           FastAPI routers (api/router.py + api/routes/*.py,
                 api/error_handlers.py) — depends on services + schemas
```

`domain/` never imports from `repositories/`, `services/`, `optimizer/`, or `api/`.
This means the optimizer engine and the database models can be unit-tested and reused
(e.g. from a CLI script) without booting FastAPI, and the API layer is a thin
translation from HTTP into a service/optimizer call and back rather than the place
business rules live. `services/` holds every business rule Module 2 needs (account
validation, ownership uniqueness, the equip/activate replacement logic) — it depends
only on `domain`/`repositories`, never on FastAPI, so it can be called from a script or
tested in isolation.

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

## Enumerations

Rarity, hero class, armor slot, and stat type are Python `enum.StrEnum` classes
(`app/domain/models/enums.py`), mapped to SQLAlchemy `Enum` columns. This means:

- Application code refers to `Rarity.LEGENDARY`, never the raw string `"legendary"` —
  a typo becomes an `AttributeError` at write-time instead of silently corrupting data.
- The database still stores a plain string column, so no custom type decoders are
  needed and the values are human-readable when inspecting the DB directly.
- The same enum is reused as the field type on the Pydantic response schemas
  (`app/schemas/hero.py` etc.), so `GET /heroes` serializes `hero_class` as the string
  value (`"warrior"`) automatically and a typo in a future filter/query param gets
  caught the same way.

`StatType` exists as its own enum (rather than one column per possible stat on `Ring`/
`Amulet`/`Pet`/`Rune`) so a new stat can be introduced by adding an enum member, not by
running a schema migration.

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
  not deferred until flush) — see `app/domain/models/user_account.py`. The
  `@validates` hook only fires on Python attribute assignment, not on a row written by
  raw SQL or a future bulk-import script — **the service layer must always derive
  `slot` from the `Armor` row itself and must never accept it as client input**, so
  this denormalized copy can't be pushed out of sync through the API surface. This is
  exactly what `ownership_service.create_armor_ownership` does (Module 2):
  `ArmorOwnershipCreate` has no `slot` field at all, so there's nothing for a client to
  override even by trying — the service fetches the `Armor` catalog row and constructs
  `UserArmorOwnership(armor=armor, ...)`, letting the `@validates` hook derive `slot`
  itself; see `tests/backend/test_api_ownership.py::test_create_armor_ownership_ignores_client_supplied_slot`.
- **Runes and skills don't need partial indexes** because a plain `UniqueConstraint`
  already does the right thing: SQL treats `NULL` as distinct from every other `NULL`
  in a unique constraint, so "not socketed" / "not equipped" rows (`NULL` index) never
  collide with each other, only with another row that claims the *same* real index. A
  `CHECK` constraint on each table additionally keeps the boolean flag and the index
  column from disagreeing (`UserRuneOwnership`: `is_equipped` iff `socket_index` is
  set; `UserSkillSelection`: `equipped_slot` set implies `is_unlocked`).

*Maximum* socket/slot **counts** (how many runes can be socketed at once, how many
skill slots exist) are still unknown pending real game data and are left to a service
layer to validate once account gear endpoints exist — the schema only enforces "no two
things in the same slot," not "no more than N things equipped."

## Value constraints

Numeric columns that should never go negative (`gold`, `gems`, `energy`, `combat_power`
on `UserAccount`; `level`, `stars`, `star_level`, `attempts`, `stars_earned` on the
ownership/progress tables) have a `CheckConstraint` at the database level. The matching
request schemas (`app/schemas/account.py`, `app/schemas/ownership.py`) mirror the same
constraints with `Field(ge=0)` / `Field(ge=1)`, so a bad request gets a 422 with a
field-level message instead of a round trip to the database just to learn gold can't be
negative — but the database constraint remains the actual guarantee, not the API
layer's validation.

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

## API layer (Module 2)

### Four layers, one direction of dependency

`api/routes/*.py` → `services/*.py` → `repositories/*.py` → `domain/models/*.py`. A
route handler validates the request (Pydantic does that automatically) and calls
exactly one service function; a service function is where "does this request make
sense right now" gets decided — does the account exist, is the display name taken, does
equipping this weapon need to unequip another one first; a repository function is pure
data access with no decisions in it at all. Nothing downstream ever imports upstream:
`repositories/` has no idea FastAPI exists, and `services/` has no idea whether it's
being called from a route, a test, or a batch script.

Two boundaries worth being explicit about, because it would be easy to blur them under
time pressure:

- **Repositories don't decide anything.** `hero_repository.get_hero` returns `Hero |
  None`; it does not raise `NotFoundError` itself. `catalog_service.get_hero` is the
  one-line wrapper that turns `None` into `NotFoundError` — because "missing means 404"
  is a decision about the request, not a fact about the database.
- **Only `app/services/equipment_service.py` touches an equip/active/slot field.**
  `HeroOwnershipUpdate`, `ArmorOwnershipUpdate`, etc. (`app/schemas/ownership.py`) don't
  even have `is_active` / `is_equipped` / `socket_index` / `equipped_slot` as fields —
  sending one in a `PATCH` request body is silently ignored, not rejected — so the only
  path that can change what's equipped is the dedicated action endpoint built to
  replace whatever was there before. This is what
  `tests/backend/test_api_ownership.py::test_update_hero_ownership_cannot_set_is_active`
  and the sibling armor-slot test check.

### Consistent error envelope

Every error response — a domain error raised in `services/`, a Pydantic validation
failure, a route that doesn't exist, or a genuine unhandled bug — comes back as
`{"error": {"type": ..., "message": ..., "details": ...}}`. `app/core/exceptions.py`
defines two exceptions services raise (`NotFoundError`, `ConflictError`; both a plain
`Exception` subclass, no FastAPI import, so they're safe to raise from anywhere in
`services/` or `repositories/`); `app/api/error_handlers.py` registers the FastAPI
exception handlers that turn each one — plus `RequestValidationError`, any
`HTTPException`, and finally the bare `Exception` catch-all — into that same shape.
A client never has to special-case "is this our error format or FastAPI's default
one"; there's only one.

**Production note:** FastAPI's debug mode (`Settings.debug`, `ARCHERO_DEBUG`) changes
this. When `debug=True` (the default — convenient for local development, where seeing
a full traceback in the browser is useful), Starlette's `ServerErrorMiddleware` renders
*its own* HTML/text traceback page for an unhandled exception instead of invoking the
registered `Exception` handler at all — the registration doesn't get ignored so much as
pre-empted by a higher-priority debug feature. That means an unexpected bug in
production, if `ARCHERO_DEBUG` were left unset, would return a raw stack trace to the
client instead of the clean `internal_error` envelope — the opposite of what "don't
leak SQL/internals" is supposed to guarantee. **Deployments must set
`ARCHERO_DEBUG=false`.** `tests/backend/test_error_handling.py`'s 500 test documents
this by constructing a `debug=False` app instance specifically, rather than using the
shared (debug-mode) test fixture, and comments explain why.

### Versioned prefix

All endpoints except `/health` are mounted under `Settings.api_v1_prefix`
(`/api/v1` by default) — `GET /api/v1/heroes` rather than a bare `GET /heroes`. This
setting existed since Module 1 specifically for this purpose; using it now means
adding a `/api/v2/...` line later doesn't require moving anything that already shipped
under `/api/v1/...`. `/health` stays unversioned since it's infrastructure (load
balancer / uptime checks), not a versioned resource.

### Pagination and filtering

Every catalog list endpoint (`GET /heroes`, `/weapons`, `/armor`, `/rings`, `/amulets`,
`/pets`, `/runes`, `/skills`, `/chapters`) takes `limit` (default 50, max 200) and
`offset` (default 0) query parameters and returns a plain JSON array — no wrapper
envelope with a total count, since nothing needs one yet and it's trivial to add
non-breaking (a new optional field) later. The `limit` ceiling exists so a catalog that
grows to thousands of rows can't be requested in one unbounded response. Most also take
an optional `rarity` filter, plus whichever filter is specific to that resource
(`hero_class` for heroes, `slot` for armor, `weapon_type` for weapons, `rune_type` for
runes, `skill_type` for skills) — applied as plain `WHERE` clauses in the repository
(`app/repositories/*_repository.py`), not client-side, so filtering scales with the
catalog rather than the response size.

### Equip actions: clear-then-set, never a separate unequip call

Every function in `app/services/equipment_service.py` (`activate_hero`, `equip_weapon`,
`equip_rune`, ...) follows the same two-step order: **first** clear whatever else
currently occupies the same slot/category for the account, **then** set the target
row's flag. That order is not incidental — the partial unique index backing "at most
one equipped" (see "Equipped-slot rules" above) would reject the moment two rows are
true at once, so the only way to get from "A is equipped" to "B is equipped" without
ever passing through an invalid intermediate state visible to a concurrent reader is to
clear first. Both steps commit together in one `db.commit()`
(`app/repositories/ownership.py::save_ownership`), so a client genuinely never needs a
separate "unequip the old one" request — that's the entire point of these endpoints
over the plain ownership `PATCH`.

Three shapes of "clear the other one," from simplest to most specific:

- **Whole-account, one boolean flag** (hero `is_active`, pet `is_active`, weapon/ring/
  amulet `is_equipped`): `ownership_repo.clear_other_equipped` — a single generic bulk
  `UPDATE` parameterized by model class and flag name.
- **Scoped by an extra column** (armor `is_equipped`, scoped to `slot` — a helmet and a
  pair of boots can both be equipped at once): the same `clear_other_equipped` helper,
  given an extra `WHERE` clause (`UserArmorOwnership.slot == instance.slot`).
- **Two columns that must agree, keyed by a numeric index rather than a boolean**
  (rune `socket_index` + `is_equipped`; skill `equipped_slot`):
  `clear_rune_socket` / `clear_skill_slot`, two purpose-built repository functions —
  genuinely different from the boolean-flag case, not just the same helper with more
  arguments, since "equip rune X into socket N" also has to handle rune X itself
  already sitting in a *different* socket (handled by simply overwriting
  `instance.socket_index` — no separate clear needed for the row being moved).

Equipping a skill additionally requires `is_unlocked` to already be true —
`equip_skill` raises `ConflictError` (409) otherwise, checked *before* anything is
cleared, so a locked-skill equip attempt never disturbs whatever was already equipped
in that slot (`tests/backend/test_api_equipment.py::test_equip_skill_failure_does_not_disturb_existing_equipped_skill`).

### The concurrent-race backstop: catching IntegrityError on equip/activate

Clear-then-set is correct *within one request*, but it does not by itself rule out two
concurrent requests each clearing-then-setting a *different* item for the same
account: both can pass their own clear step before either commits, so both attempt to
set `is_equipped`/`is_active` true (or claim the same rune socket / skill slot) at
once. Module 1's partial unique indexes are the actual backstop here, not application
logic — one of the two commits will fail with `IntegrityError`, so the corrupted
"both equipped" state can never be persisted. The gap this review round found and
fixed was what happened *next*: every `equip_*`/`activate_*` function in
`equipment_service.py` now wraps its `save_ownership` call in `try/except
IntegrityError`, translating it to `ConflictError` (409) via the shared
`app/services/errors.py::raise_conflict_from_integrity_error` — the same helper
`ownership_service.py`'s `create_*` functions use for duplicate-ownership conflicts.
Before this, that failure reached the generic `Exception` handler and returned an
unhelpful 500; a concurrent uniqueness violation is exactly the kind of thing a client
should see as a clean, retryable 409. `unequip_*`/`deactivate_*` don't need the same
wrapping — clearing a flag to `False`/`NULL` can never violate a partial unique index
that only constrains `True`/non-`NULL` rows.

`tests/backend/test_equipment_conflict_race.py` verifies this for all eight
equip/activate actions by monkeypatching the relevant `clear_*` repository call to a
no-op (standing in for "a concurrent request's clear already ran"), pre-arming a
conflicting row, and asserting a 409 rather than a 500. True thread-level concurrency
remains untested — a known, deliberate scope boundary rather than an oversight, and one
worth revisiting if this API ever needs to prove behavior under real concurrent load
rather than just its effect.

### Testing FastAPI against the in-memory SQLite fixture

`tests/backend/conftest.py`'s `client` fixture overrides the `get_db` dependency to
reuse the *same* Python `Session` object the test uses to seed data, so
`db.add(...); db.commit()` in a test is immediately visible to the API call that
follows. This surfaced a real bug while building Module 2: FastAPI runs synchronous
route handlers in a worker thread, and SQLAlchemy's default pool hands each *thread* —
not each connection request — its own SQLite connection. For a file-based database
that's harmless (every thread's connection opens the same file), but for
`sqlite:///:memory:` each connection *is a separate, empty in-memory database*, so the
endpoint's worker thread saw a different, table-less database than the one the test
had just seeded. `app.db.session.build_engine` now passes `poolclass=StaticPool` for
in-memory SQLite URLs specifically — one connection, shared and reused everywhere —
which is the standard fix for exercising an in-memory SQLite database from a
multi-threaded app. File-based SQLite and PostgreSQL are unaffected.

## The Optimizer Engine (Module 3)

### What it is, and what it deliberately is not

Archero 2 Optimizer never automates gameplay, controls the game, sends input, reads
the game's memory, or modifies the game in any way — the player always plays manually.
The Optimizer Engine's only job is to look at data the player's account already has
(hero, gear, runes, skills, chapter progress) and turn it into a recommendation: which
of several options is best *for this build*, and why. Module 3 ships the first
concrete advisor built on this engine — the Skill Advisor, `POST
/optimizer/skills/advise` — but the engine itself is designed to carry a Gear Advisor,
Farm Advisor, Upgrade Advisor, Rune Advisor, and Resource Advisor later without being
rewritten.

### Why `app/optimizer/` is its own top-level package, not a module under `services/`

Earlier notes in this file (and the original Module 2 write-up) assumed the scoring
engine would live inside `services/`. Building it surfaced a real reason not to:
`services/` functions are characterized by needing a `Session` and raising
`NotFoundError`/`ConflictError` — they are inherently request-shaped. The optimizer's
actual decision logic (given a build's stats, which of these candidates scores
highest, and why) has no reason to need a database at all — it is a pure function of
numbers. Keeping that logic under `services/` would mean every future consumer the
spec explicitly calls out — a mobile app, an overlay, a screenshot-analysis pipeline —
would either have to go through a `Session`-shaped API it doesn't need, or the "pure"
and "DB-aware" pieces would end up tangled in the same module out of proximity. A
sibling top-level package makes the boundary a directory, not a convention someone has
to remember: `context.py`, `engine.py`, `weights.py`, and `results.py` import nothing
but `app.domain` (models and enums) — no `Session`, no FastAPI — and only the
`advise_for_account`-style wrapper at the bottom of each advisor module touches a
database, by calling into the *existing* `services/` (`account_service`,
`catalog_service`) rather than repositories directly, so account-lookup rules
(`NotFoundError` on a missing account/skill) stay defined in exactly one place.

### Layering inside `app/optimizer/`

```
app/optimizer/
  weights.py           every tunable constant, GAME DATA PLACEHOLDER — see below
  context.py           BuildContext (a snapshot of one account's aggregated stats)
                        + build_context(account) to construct one from ORM data
  engine.py             the shared scoring primitives every advisor is built from:
                        offense_score, defense_score, mobility_score, utility_score
  results.py            ScoredOption[T] / AdvisorResult[T] — the generic "ranked
                        options with reasons" shape every advisor reports in
  advisors/
    skill_advisor.py    the first concrete advisor: score_skill, advise, and the
                        DB-aware advise_for_account wrapper
```

**`BuildContext`** is the one thing every advisor scores candidates against: an
immutable snapshot of an account's aggregated attack/defense/hp/speed/crit/dodge/
resource-gain, built once by `build_context()` from the active hero, equipped weapon,
equipped armor pieces, equipped rings/amulets, active pet, and equipped runes (each
scaled by its own level/star factor), plus the account's current chapter (for
`power_gap_ratio`, i.e. how over/under-powered the account is for where it currently
is). It requires no database of its own — it's built once from an already
eager-loaded `UserAccount` (see `app/repositories/account_repository.get_account_with_detail`,
extended in this module to eager-load every ownership type's catalog relationship so
`build_context` never triggers a lazy-load) and is plain data from then on.

**`engine.py`**'s four scoring primitives (`offense_score`, `defense_score`,
`mobility_score`, `utility_score`) are the actual "decision engine" every advisor is
built from — each reduces a `BuildContext` to one number summarizing a dimension of
the build. The Skill Advisor combines them by candidate skill type; a future Gear
Advisor would compare these same primitives across a *hypothetical* `BuildContext` per
candidate item; a Farm Advisor would weigh `utility_score` against a chapter's energy
cost. If a new advisor needs a dimension not covered here, the primitive belongs in
`engine.py`, not duplicated inside that advisor's own module — that is what "all
advisors reuse the same decision engine" means concretely.

**`results.py`** is deliberately *just* a data shape (`ScoredOption[T]`:
option/score/reasons; `AdvisorResult[T]`: a ranked tuple plus a `.recommended`
property), not a forced common interface. A skill choice, a future gear choice, and a
future farming-route choice don't share an input shape or a lookup path, so a common
`Advisor` abstract base class behind one real implementation would be premature
abstraction over a single concrete case. What's actually shared across advisors is the
`engine.py` primitives and this reporting shape — every advisor returns "ranked
options, best first, each with human-readable reasons" — not a forced
`Advisor.recommend()` method signature.

**`weights.py`** centralizes every tunable number the scoring formulas use (how much a
level or star adds, how much an offensive/defensive/utility/movement skill's synergy
bonus is worth, the "expected" defense baseline a defensive pick is compared against).
Like the catalog enums in `app/domain/models/enums.py`, these are explicitly marked
**GAME DATA PLACEHOLDER** — realistic-shaped numbers chosen so the engine is fully
functional today, not measurements from the real game. Centralizing them in one module
means re-tuning the whole engine against real game data later is a one-file change,
not a hunt through every advisor for a hardcoded constant.

### Why the Skill Advisor never uses a static tier list

`score_skill` never branches on a skill's *name*. Every candidate gets a small
tier-based baseline (`weights.SKILL_TIER_BASE_VALUE * skill.tier`) plus a
*build-simulated marginal gain* — see "Module 3.1: effect-based marginal scoring"
immediately below for what that means and why the original category-based version of
this section was replaced.

## Module 3.1: effect-based marginal scoring

Module 3 shipped with `score_skill` branching on a candidate's `skill_type`
(offensive/defensive/utility/movement) — an offensive skill scored higher the harder
the build already hit, a defensive skill scored higher the squishier the build was, and
so on. A review of that version correctly identified its ceiling: **every skill of the
same type and tier scored identically.** Multishot, Ricochet, and Attack Up — all
OFFENSIVE, all tier 3 — got the exact same number for any given build, because nothing
in the model looked past `skill_type`/`tier`. The engine could answer "is an offensive
pick good for this build" but not "is *this* offensive pick better than *that* one,"
which is the actual question a player asks when the game offers a specific named
choice. Module 3.1 replaces the category-branching formula with a marginal
build-simulation model that answers the second question.

### The mechanism: simulate the pick, then measure the difference

1. **`SkillEffect`** (`app/domain/models/skill_effect.py`) gives a `Skill` catalog row
   zero or more structured, typed effects — `EffectType.PROJECTILE_COUNT`,
   `BOUNCE_COUNT`, `ATTACK_SPEED_MULTIPLIER`, and so on
   (`app/domain/models/enums.py`) — instead of only a `skill_type` category. This is
   what actually distinguishes Multishot (`PROJECTILE_COUNT`) from Ricochet
   (`BOUNCE_COUNT`) from Attack Up (`ATTACK_SPEED_MULTIPLIER`) at the data level. One
   row per effect, not a column per possible effect on `Skill`, so a skill can carry
   more than one effect and a new effect type never needs a migration touching `Skill`
   itself — the same reasoning that gave `Ring`/`Amulet`/`Pet` a generic `StatType`
   instead of one column each.
2. **`BuildContext`** (`app/optimizer/context.py`) gained `projectile_count` (baseline
   `1.0` — every build has at least one projectile) and `bounce_count` (baseline
   `0.0`), plus `selected_skill_ids`. `build_context()` now folds the effects of the
   account's *already-equipped* skills (`UserSkillSelection.equipped_slot is not
   None` — the same "equipped, not merely unlocked/owned" test every other ownership
   type in this project uses) into these fields, the same way it already folded in
   equipped gear. This is what makes an account's existing skill choices part of its
   build, not invisible to it — the review's second-biggest finding.
3. **`app.optimizer.simulator.apply_skill(context, skill)`** (new, pure, no I/O)
   projects one *candidate* skill's effects onto a **copy** of a `BuildContext` — same
   field-mapping table (`context._EFFECT_TYPE_FIELD`) `build_context` uses for
   already-equipped skills, just applied to a hypothetical addition instead of the
   real baseline.
4. **`app.optimizer.objectives.ObjectiveProfile`** (new) is a named weighting of
   `engine.py`'s dimensions into one scalar — `BALANCED`, `BOSS` (weights single-target
   `offense_score` heavily), `FARM` (weights the new `aoe_score`/`utility_score`
   heavily), `SURVIVAL` (weights `defense_score` heavily). "What good means" depends on
   what the player is actually doing right now, which a single fixed formula can't
   express.
5. **`score_skill`** (`app/optimizer/advisors/skill_advisor.py`) now computes
   `objective.evaluate(context)` before and after `simulator.apply_skill`, and the
   *difference* — not a category-based synergy formula — is the skill's marginal
   value, added on top of the tier baseline. A skill with no `SkillEffect` rows yet
   simply has zero marginal gain and falls back to tier-only scoring — an honest,
   graceful degradation rather than a crash, exercised by
   `tests/backend/test_optimizer_skill_advisor.py::test_skill_with_no_effects_falls_back_to_tier_only_score`.

`engine.py` gained one new primitive, `aoe_score`, rather than being thrown away —
single-target `offense_score` doesn't capture "hits multiple enemies at once," which is
exactly what `PROJECTILE_COUNT`/`BOUNCE_COUNT` effects are for. It scales by `sqrt` of
the extra projectile/bounce count, not linearly: the first extra projectile covers
proportionally more new ground than the fifth, and — not incidentally — this is the
concrete mechanism by which an account's *already-selected* skills change how much a
*new*, similar one is worth (a second `PROJECTILE_COUNT` pick has a smaller marginal
`aoe_score` gain than the first), which
`test_existing_selected_skill_reduces_marginal_value_of_a_similar_new_one` proves
directly. `PROJECTILE_AOE_FACTOR` and `BOUNCE_AOE_FACTOR` (`weights.py`) are
deliberately different constants specifically so a projectile-count skill and a
bounce-count skill of identical tier don't collapse back to the same score —
`test_same_type_same_tier_skills_can_rank_differently` is the test that exists purely
to keep this property true.

### Two audiences for "why": `summary` versus `reasons`

`ScoredOption` (`app/optimizer/results.py`) gained a `summary: str` field alongside the
existing `reasons: tuple[str, ...]`. They answer different questions for different
readers: `summary` is one player-facing sentence ("Ricochet mainly boosts your
bounce/ricochet count — estimated farm objective value for your current build:
+1.4."); `reasons` is the field-by-field numeric breakdown a developer debugging a
recommendation would want. Neither is derived from the other by truncating — a review
finding was that the original single `reasons` list was useful for debugging but not
phrased for a player, and collapsing both audiences into one field would keep serving
neither well.

### Deterministic tie-breaking

`advise()` now sorts by `(-score, skill.id)` instead of score alone. Two skills that
happen to score identically (most visibly, two skills with no modeled effects and the
same tier) previously kept whatever relative order they arrived in the candidate list —
meaning `["Multishot", "Ricochet"]` and `["Ricochet", "Multishot"]` could recommend
different skills for an identical build, which is not intelligence, it's request-order
sensitivity. `test_advise_breaks_score_ties_deterministically_by_skill_id` locks this
down.

### What Module 3.1 deliberately still does not do

The review that motivated this module also raised hero/weapon *identity* (`Ricochet
works especially well with Dragon Bow`) and named-tag synergies between specific
skills and specific gear. That is not implemented: it requires real data about which
tags mean what for which weapons/heroes, which — like every other placeholder value in
this project — does not exist yet, and inventing plausible-looking tag data would be
indistinguishable from the static tier list this whole engine exists to avoid. The
mechanism built here (structured effects, marginal simulation, objective profiles)
is designed to carry that once real data exists — a weapon-specific synergy would be
another `EffectType`-like structured fact feeding the same `apply_skill`/`evaluate`
pipeline, not a different architecture. Talents, inventory, and resources (also named
in the original Module 3 spec) are likewise not yet part of `BuildContext` and are left
for a future pass once those catalog entities exist.

One naming difference from the review's suggested `BuildSnapshot`/`BuildSimulator`/
`ScoreBreakdown` class names worth calling out explicitly: this module uses module-level
functions (`simulator.apply_skill`, `objectives.ObjectiveProfile.evaluate`) and the
existing `BuildContext`/`ScoredOption` dataclasses rather than new classes for each
concept. That mirrors `engine.py`'s existing style (plain functions over a `BuildContext`,
no class hierarchy) rather than a deliberate rejection of the review's design — the
behavior described in the review is what's implemented, under the project's established
naming conventions instead of new ones introduced for this module alone.

## Frontend architecture (Module 4)

### Why My Account and Build Optimizer only, functionally

The frontend (`frontend/`, React + TypeScript + Vite + Tailwind) has routes for all five
pages from the original spec, but only **My Account** and **Build Optimizer** call real
endpoints. **Dashboard**, **Upgrade Advisor**, and **Settings** render a shared
`PlaceholderPage` explaining what backend piece is missing (an account-wide scoring
model; a Gear/Upgrade/Resource Advisor; a weights read/write endpoint) instead of
displaying invented numbers. This mirrors the project's core rule for the backend's own
`GAME DATA PLACEHOLDER` values — never present a placeholder as if it were real data —
applied to the frontend: a page that *looks* functional but returns fabricated numbers
would be worse than an honest "not built yet" screen, since a player could act on it.

### No client-side data model beyond the API's own shapes

`src/lib/types.ts` is a set of plain TypeScript interfaces mirroring the backend's
Pydantic schemas by hand — there is no OpenAPI codegen step. `src/lib/apiClient.ts` is a
thin `fetch` wrapper (`api.listHeroes()`, `api.addHero(...)`, `api.adviseSkills(...)`,
...) whose only real job is unwrapping the backend's one error envelope shape
(`{error: {type, message, details}}`, see "Consistent error envelope" above) into a
throwable `ApiError` — every page catches that and shows `error.message` directly,
rather than each page re-implementing envelope parsing. If the backend and frontend
types drift, a wrong field name fails loudly at runtime (`undefined` where a value was
expected) rather than silently — an accepted tradeoff for a project this size without
generated types.

### No account list endpoint, so "current account" lives in the browser

The backend has no `GET /accounts` (list) endpoint and no auth/session concept (see
"API layer" above) — nothing server-side represents "which account the user is looking
at right now." `useCurrentAccount` (`src/hooks/useCurrentAccount.ts`) tracks that choice
in `localStorage` instead, shared between the My Account and Build Optimizer pages so
switching between them keeps the same account selected. Switching to a different
account ID verifies it exists (`GET /accounts/{id}`) before adopting it, rather than
trusting an arbitrary client-typed number.

### One generic ownership section, two that couldn't be

Six of the seven ownership types (hero, weapon, armor, ring, amulet, pet) share the
exact same shape: own something from a catalog, optionally give it a level/star, equip
or unequip it, remove it. `src/components/OwnershipSection.tsx` is one component
parameterized by that shape, instantiated six times in `MyAccountPage.tsx` — the same
"one generic thing, not six near-identical copies" reasoning the backend used for
`ownership_repo.clear_other_equipped`. Runes (equip needs a `socket_index`) and skill
selections (equip needs an `equipped_slot`, plus an `is_unlocked` gate before a skill
can be equipped at all, and no level/star fields) are genuinely different shapes, not
just the same one with more props threaded through — they get their own
`RuneSection.tsx`/`SkillSelectionSection.tsx` rather than being forced into
`OwnershipSection`, the same "don't force a shared abstraction where the underlying
problem actually differs" call the backend made for rune/skill equip logic
(`clear_rune_socket`/`clear_skill_slot` versus the generic `clear_other_equipped`).

Every mutation (add/update/remove/equip/unequip) re-fetches the whole account detail
afterward rather than patching local state optimistically — equip actions can silently
change *other* rows (clear-then-set replaces whatever was previously equipped), so the
only way to stay correct is to ask the server what's true now, the same reason the
backend's own equip endpoints return the full updated resource rather than a diff.

### What's not decided yet

A Rune Advisor and Resource Advisor from the original Module 3 spec are still not
built — Module 5 (below) implemented Gear, Upgrade, and Chapter Advisors, but a
standalone rune-socketing recommender and a resource-spending recommender remain
future modules once there's a concrete resource model to reuse from Upgrade Advisor
(see "Gold as the one upgrade currency" below). The weighting model in `weights.py` in
particular is meant to be revisited once real game data is available — see the root
README's "Game data" section.

## Module 5: Gear, Upgrade, and Chapter Advisors

Module 5's spec was explicit that no new decision engine may be created — Gear,
Upgrade, and Chapter Advisors all have to be built the same way Skill Advisor is: pure
`score_*`/`advise` functions over a `BuildContext` and an `ObjectiveProfile`, plus a
DB-aware `advise_for_account` wrapper, reusing `engine.py`/`simulator.py` rather than
each inventing its own notion of "how much is this worth." Getting there required
generalizing three pieces of `skill_advisor.py` that were originally written
skill-specific, then building each new advisor directly on the generalized version —
not parallel, independently-written logic that happens to look similar.

### Generalizing "simulate a change": `context.py`'s contribution functions

`build_context()` used to compute each equipped item's stat contribution inline, as
one-off arithmetic inside its own loop bodies — correct for "what does the account
have right now," but useless for "what would owning a *different* item, or the *same*
item at a higher level, look like," which is exactly what Gear Advisor and Upgrade
Advisor need to answer. `context.py` now exposes that arithmetic as standalone, pure
functions — `hero_contribution(hero, level)`, `weapon_contribution(weapon, level,
star_level)`, `armor_contribution(armor, level, star_level)`,
`stat_item_contribution(stat_type, value, level)` (shared by ring/amulet/pet — same
"one `StatType` and magnitude, scaled by level" shape for all three),
`rune_contribution(rune_type, effect_value, level)`, and `skill_effect_contribution(skill)`
— each taking a catalog row plus whatever level/star it should be evaluated at, not an
ownership row specifically. `build_context()` now calls these same functions for
whatever is *currently* equipped (via a small `_add(contribution)` accumulator), and
Gear/Upgrade Advisors call the exact same functions for owned-but-unequipped items or
hypothetical higher levels. There is exactly one formula for "how much attack does a
weapon at level 5, 2 stars add," not a copy living inside `build_context` and a second,
subtly-different one inside the new advisors.

### Generalizing "apply the change": `simulator.replace_contribution`

`simulator.py` used to have exactly one function, `apply_skill`, specific to "add a
skill's effects on top of the baseline." Module 5 generalized it to
`replace_contribution(context, before, after)` — given what a build currently gets
from something (`before`) and what it would get instead (`after`), both as
`{field_name: value}` dicts, it returns a new `BuildContext` with the difference
applied via `dataclasses.replace`, changing nothing when `before == after`. Every
advisor's "simulate this candidate" step is one call to it, with `before`/`after`
meaning something different per advisor but the mechanism identical:

- **Skill Advisor**: `before={}`, `after=skill_effect_contribution(candidate_skill)` —
  purely additive, since picking a new skill never removes an existing one.
  `apply_skill` is now a two-line wrapper around this call, kept only because
  "apply_skill" reads better at its own call sites than a raw `replace_contribution`
  invocation would.
- **Gear Advisor**: `before=<what's currently equipped contributes>`,
  `after=<what this candidate would contribute>` — a genuine swap, since equipping one
  weapon un-equips whatever was there.
- **Upgrade Advisor**: `before=<item at its current level>`, `after=<the same item at
  the highest level the account can currently afford>` — a swap against itself at a
  different level, not a different item.

### Generalizing "explain the change": `explanations.py`

`skill_advisor.py` originally had its own private `_FIELD_DESCRIPTION`/
`_changed_fields`/`_summarize` helpers for turning a before/after `BuildContext` pair
into player-facing text. Gear and Upgrade Advisors needed exactly the same thing, so
that logic moved out into `app/optimizer/explanations.py` — the shared "explanation
system" the Module 5 spec asked for by name — and `skill_advisor.py` was refactored to
call it rather than keep its own copy (proving the extraction was genuine reuse, not
just aspirational sharing). `changed_fields(before, after)` diffs every field
`FIELD_DESCRIPTION` knows how to describe; `dominant_field` picks the single largest
mover for a one-sentence summary; `build_reasons`/`build_summary` render the numeric
`reasons` breakdown and the player-facing `summary` sentence respectively, honestly
saying "no measurable stat change" rather than inventing something to say when a
candidate's effects don't move any tracked field. Chapter Advisor is the one exception
— scoring a chapter isn't a before/after `BuildContext` diff at all (see below), so it
builds its `reasons`/`summary` by hand instead of forcing that shape onto a genuinely
different kind of question.

### `objectives.resolve`: one place that turns a bad objective name into 404

All four advisors accept an `objective_name: str` at their `advise_for_account`
boundary and need the identical "look it up in `BY_NAME`, or raise `NotFoundError`"
handling. That's now `objectives.resolve(name)`, replacing what had started as a
copy-pasted `try/except KeyError` in each advisor module.

### Gear Advisor: comparing owned items, no tier list

`app/optimizer/advisors/gear_advisor.py` ranks an account's *owned* weapons, armor
(scoped to one `ArmorSlot` at a time — a helmet and a pair of boots never compete),
rings, amulets, or pets. Candidates always come from the account's own ownership rows,
never a client-submitted id list the way Skill Advisor's `candidate_skill_ids` works —
there is no "equip an item you don't have" in this game, so what's biddable is entirely
determined by what's owned. `score_item` builds a hypothetical `BuildContext` with
`replace_contribution` (swapping the currently-equipped item's contribution for the
candidate's) and scores that hypothetical context directly with the chosen
`ObjectiveProfile` — an absolute score, not a delta, since real gear already has real
numbers and needs no tier-based baseline to fall back on the way an effect-less skill
does. "Switching to a worse item scores lower than keeping the current one" falls out
of this for free: the currently-equipped item is just another candidate scored the same
way, not a specially privileged baseline.

### Upgrade Advisor: gold as the one upgrade currency, worthless upgrades filtered out

`app/optimizer/advisors/upgrade_advisor.py` considers leveling up any owned hero,
weapon, armor piece, ring, amulet, pet, or rune. The spec's example currency ("40
Weapon Scrolls") assumes a scroll economy that doesn't exist yet in this project's
domain model (`UserAccount` has `gold`, not per-category scroll counts) — rather than
inventing a fictional scroll resource, gold is used as the one real, already-modeled
upgrade currency, with `weights.BASE_UPGRADE_COST_PER_LEVEL` (a **GAME DATA
PLACEHOLDER**, like every other tunable in `weights.py`) standing in for whatever the
real per-item gold/scroll cost curve turns out to be. `max_affordable_levels` computes
how many levels of `BASE_UPGRADE_COST_PER_LEVEL * level` the account's current gold
covers, capped at `weights.MAX_UPGRADE_LEVELS_CONSIDERED` — an item that can't even
afford one level is never scored at all, not scored low. `score_upgrade` reports its
`score` as the *percentage* build improvement (`(after - before) / before * 100`),
matching the spec's own example phrasing ("Expected build improvement: +8.7%")
directly rather than a raw objective-score delta. "If an upgrade isn't optimal, it
must not be recommended" is enforced in `advise_for_account`, not `advise`: `advise()`
still ranks whatever candidates it's given (raising `ValueError` for an empty list, the
same contract every advisor's pure function keeps), but `advise_for_account` filters
the *result* down to `score > 0` afterward, raising `NotFoundError` if nothing
affordable is actually worth doing — an affordable-but-worthless upgrade never reaches
the ranking a client sees.

### Chapter Advisor: two genuinely different questions, one shared mechanism

`app/optimizer/advisors/chapter_advisor.py` answers both "best chapter to farm" and
"best chapter to clear next" — deliberately *not* the same formula reused with
different weights, because they're different questions: farming wants somewhere
comfortable and cheap to repeat; progression wants the *furthest* chapter still safely
reachable at all. `app/optimizer/chapter_scoring.py` holds the primitives this needs,
kept separate from `engine.py` because they're functions of `(BuildContext, Chapter)`,
not `BuildContext` alone the way every `engine.py` primitive is:
`power_gap_for_chapter` (a per-chapter version of `BuildContext.power_gap_ratio`),
`clear_safety(gap)` (0.0 at or below `weights.MIN_SAFE_POWER_GAP_RATIO`, ramping
linearly to 1.0 at the chapter's recommended power), `farm_suitability` (the build's
`ObjectiveProfile`-weighted strength, scaled down by clear safety and by energy cost —
a chapter that costs more energy per attempt is worth less per unit of grinding time),
and `progression_suitability` (rewards a *further* chapter's recommended power, but
only in proportion to how safely reachable it currently is — an unreachable chapter
scores 0 regardless of distance, never "the furthest option anyway"). `score_chapter`
picks between the two formulas by checking `objective.name == "farm"` — the same
`ObjectiveProfile` every other advisor takes, since "farm" already means "weigh
resource efficiency over raw single-target power" everywhere else in the engine, so
reusing it here for "which chapter" rather than "which skill/gear/upgrade" is the same
concept applied to a new dimension, not a new one invented for this advisor.

**Composing with Upgrade Advisor for the "upgrade first" case.** When the top
*progression* pick (`objective.name != "farm"`) is currently unsafe
(`clear_safety <= 0` — the account is under-powered for it), `advise_for_account`
cross-calls `upgrade_advisor.advise_for_account` and folds its top recommendation into
that chapter's `summary`/`reasons` (`_with_upgrade_suggestion`), producing exactly the
spec's example shape ("Recommendation: Upgrade weapon first... Then continue on
Chapter 24") without a new response shape or a second, chapter-advisor-local copy of
"what's the best upgrade right now" logic. If nothing is currently affordable or
worthwhile to upgrade either, the chapter recommendation is returned as-is (the
cross-call's `NotFoundError` is caught, not propagated) — an accurate "here's the
best chapter, no upgrade advice available right now" is better than a hard failure
for a real, valid account state. Farm mode never triggers this cross-call at all: an
unsafe farming target isn't the "you're behind, upgrade first" signal progression mode
needs — farming already picks the safest chapter available by construction.

### API and tests

All three advisors are wired up the same way Skill Advisor is: `POST
/api/v1/optimizer/gear/advise`, `/upgrade/advise`, and `/chapters/advise`
(`app/api/routes/optimizer.py`), each a thin translation from its `AdvisorResult[T]`
into a `*AdviceResponse`/`*ScoreBreakdown` pair (`app/schemas/optimizer.py`) — no
decision logic in the route handlers themselves. `GearAdviceRequest` uses a
`@model_validator` to reject (422) an `armor` category request with no `armor_slot`,
mirroring how `equipment_service.equip_armor` itself requires a slot to scope
replacement. `tests/backend/test_optimizer_contribution_functions.py`,
`test_optimizer_simulator.py`, `test_optimizer_explanations.py`,
`test_optimizer_gear_advisor.py`, `test_optimizer_upgrade_advisor.py`, and
`test_optimizer_chapter_advisor.py` cover the new pure functions and DB-aware
`advise_for_account` paths directly; `test_api_optimizer.py` covers all three new
endpoints' happy paths, 404s (missing account, unknown objective, nothing owned/
affordable, empty chapter catalog), and the armor-without-slot 422 — the same shape of
coverage Skill Advisor already had.

### What's not decided yet

The Gear/Upgrade/Chapter Advisor frontend pages don't exist yet — Module 4 only wired
up My Account and Build Optimizer against real endpoints, so Dashboard/Upgrade
Advisor/Settings remain the honest placeholders described above until a future module
gives them real pages to call these new endpoints from.

## Module 6: real rune data, and the stat dimensions it revealed

Every number in this project before Module 6 was an explicitly-labeled **GAME DATA
PLACEHOLDER** — realistic-shaped, but not sourced from the real game (see the root
README's "Game data" section). Module 6 is the first module to seed real data,
sourced from screenshots of a live Archero 2 account's "Rune Workshop" and account
stat "Details" screens. Real data immediately exposed a real gap: the live game
tracks per-summon-type damage bonuses (Circle, Sprite, Plant, Ice, Poison, Lightning,
Fire — one per rune-granted companion or elemental proc) and a flat "ATK PWR" /
"Main Weapon DMG" bonus, none of which existed as `BuildContext` fields or
`EffectType` members before this module. Rather than lossily mapping these onto the
nearest existing field (which would have quietly collapsed a Circle-build and a
Plant-build to the same "attack" number — precisely the kind of same-category
collapse Module 3.1 already fixed once for skills), this module extends the model the
same way Module 3.1 did: new structured effect types, new `BuildContext` fields, no
new scoring formula.

### `EffectType` gained eight members, `BuildContext` gained seven fields

`ATTACK_BONUS`, `CIRCLE_DAMAGE_BONUS`, `SPRITE_DAMAGE_BONUS`, `PLANT_DAMAGE_BONUS`,
`ICE_DAMAGE_BONUS`, `POISON_DAMAGE_BONUS`, `LIGHTNING_DAMAGE_BONUS`, and
`FIRE_DAMAGE_BONUS` join `app/domain/models/enums.py::EffectType`, each mapped
(`app/optimizer/context.py::_EFFECT_TYPE_FIELD`) to a `BuildContext` field —
`ATTACK_BONUS` reuses the existing `attack` field (see "One simplification, stated
plainly" below), the other seven are new: `circle_damage`, `sprite_damage`,
`plant_damage`, `ice_damage`, `poison_damage`, `lightning_damage`, `fire_damage`, all
defaulting to `0.0`. This is purely additive to the existing model — no existing
field, formula, or advisor changed shape; a build that never invests in a Plant
Guardian summon simply keeps `plant_damage == 0.0` and nothing downstream needs to
know these fields exist at all yet (no advisor currently scores by them — see "What
Module 6 deliberately still does not do" below).

### `Rune` gained structured multi-effect rows, the same way `Skill` did in Module 3.1

Before this module, `Rune` had a single `effect_value: float` column and an
`effect_description` text field, implicitly assuming one rune grants one number.
The real rune data immediately falsified that: a single rune (e.g. Vine Bind) grants
*several* effects simultaneously (`PLANT_DAMAGE_BONUS`, twice, at different
magnitudes, plus `ATTACK_BONUS`). `app/domain/models/rune_effect.py::RuneEffect` is a
new table mirroring `SkillEffect` exactly (one row per effect, `ondelete="CASCADE"`
from its rune, a `value >= 0` check) — the same "don't force one scalar column to
represent N things" reasoning, applied to the second catalog entity that turned out
to need it. `Rune.effect_value` is gone; `Rune.effects: list[RuneEffect]` replaces it,
and `Rune.effect_description` stays as free text for qualitative abilities that don't
reduce to a flat number (see "One simplification, stated plainly" below).

One real difference from `SkillEffect`, not just a rename: **runes level up, skills
don't.** `skill_effect_contribution(skill)` applies every effect at full value with
no level parameter, because a skill choice has no level. `rune_effect_contribution(
rune, level)` (`app/optimizer/context.py`) scales every effect by the same
`_level_multiplier(level)` every other leveled contribution function
(`hero_contribution`, `weapon_contribution`, ...) uses — genuinely different math for
a genuinely different mechanic, not the same function copy-pasted.

### One simplification, stated plainly: `ATTACK_BONUS` folds two real mechanics into one field

The source data distinguishes "ATK PWR" (a rune stat that, per one rune's own
description, other runes can *convert* percentages of — "Converts 15% ATK PWR to 20%
Max HP") from "Main Weapon DMG" (which several rune descriptions separately call out
as boosting only the auto-attack, not summons). This project's `BuildContext.attack`
is a single flat number with no separate "power stat other things scale off of"
concept and no multiplicative conversion mechanism — modeling that distinction
correctly would mean rebuilding how `attack` is computed everywhere, not adding an
enum member. `ATTACK_BONUS` therefore folds both into the existing `attack` field
additively. This is a real, acknowledged simplification (documented on the
`EffectType` enum itself), not a silent one — the alternative, inventing plausible-
looking numbers for a mechanic this project doesn't model yet, is exactly the kind of
thing the "never present a placeholder as real data" rule exists to rule out.
Percentage-based effects in the source data ("Fire DMG +50%", "Main weapon DMG
+10%", stat-conversion abilities) are recorded as free text in `effect_description`
for the same reason: `RuneEffect.value` is a flat additive number, and there is no
percentage-modifier field to put a "+50%" into without misrepresenting it as flat.

### `database/seeds/`: the first real seed data, and why the logic lives under `app/`

`app/seeds/runes.py` (new top-level package, depends only on `domain`) holds the
actual seed data and the idempotent `seed_runes(db)` function; `database/seeds/
seed_runes.py` is a two-line CLI wrapper that just calls it. Splitting it this way —
rather than putting everything in the `database/seeds/` script directly — means the
seed data gets the project's normal ruff/mypy/pytest coverage (`tests/backend/
test_seed_runes.py` verifies it inserts exactly the expected rows, is idempotent on a
second run, and — the check that matters most — that summing each seeded rune's
numeric effects by type reproduces the *account-level* aggregate totals shown in the
same source screenshots exactly (e.g. every rune contributing `CIRCLE_DAMAGE_BONUS`
sums to the account's displayed "Circle DMG +30"). That reconciliation is what turns
this from "plausible-looking example data" into a verified transcription of a real
account state, and it would fail loudly if a future edit to the seed data broke the
match.

`seed_runes` is intentionally **insert-if-missing by name**, not an upsert: re-running
it after a schema change or alongside a future seed script never duplicates or
silently overwrites a row that may have been hand-edited since.

### What Module 6 deliberately still does not do

The seven new per-summon-type damage fields are **plumbed through `BuildContext` and
`build_context()` but not yet consumed by any advisor's scoring formula** —
`engine.py`'s `offense_score`/`aoe_score`/etc. and every `ObjectiveProfile` still only
read the pre-existing fields. Wiring "does this build's Circle/Plant/... investment
matter for this objective" into the scoring formulas is real design work (which
summons a Farm-oriented player actually leans on, how they should trade off against
raw `attack`) that real gameplay data doesn't yet answer, so it's left for a future
pass rather than guessed at now — the same "don't invent plausible-looking numbers"
principle applied to a formula instead of a data value. Heroes, weapons, armor,
rings, amulets, pets, skills, and chapters still have zero seeded rows — runes are the
first catalog entity with real data, not the last one needed; see the root README's
"Game data" section for what's still outstanding.
