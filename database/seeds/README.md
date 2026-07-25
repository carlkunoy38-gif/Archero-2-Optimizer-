# Seed scripts

Catalog seed data, sourced from real Archero 2 screenshots as it becomes available —
see `database/README.md` and the root README's "Game data" section for which
catalog entities still have none.

- `seed_runes.py` — the first entry, seeding 10 real runes (Spin SPD Up, Sharp Arrow,
  Flamenox Seal, Vine Bind, Flamenox Touch, Circle, Frostshock Touch, Melee Sprite,
  Resilience, Intelligence) with their real numeric effects. The actual seed data and
  logic live in `backend/app/seeds/runes.py` (part of the `app` package, so it gets
  the project's normal ruff/mypy/pytest coverage); this script is a thin, directly
  -runnable CLI wrapper around it. See `runes.py`'s own docstring for exactly what's
  real data versus a placeholder (`rarity` isn't readable from the source
  screenshots, so it's a reasonable guess, not a transcription).

Run a seed script against whichever database `ARCHERO_DATABASE_URL` points at
(defaults to the dev SQLite file — see `docs/installation.md`), from `backend/` so
the `app` package resolves:

```bash
cd backend
python ../database/seeds/seed_runes.py
```

Every seed script here is idempotent (safe to re-run — already-present rows by name
are skipped, never duplicated) and populates data purely through the SQLAlchemy
models in `backend/app/domain/models/`, never raw SQL, so it stays valid as the
schema evolves. See `tests/backend/test_seed_runes.py` for the pattern new seed
logic's tests should follow, including reconciling seeded totals against the real
account screenshot they were sourced from.
