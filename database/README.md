# database/

In development, this directory holds the SQLite database file
(`archero2.db`, gitignored) that the backend reads and writes by default —
see `backend/app/core/config.py` for how the path is resolved and
`docs/installation.md` for how to switch to PostgreSQL.

## seeds/

Reserved for catalog seed data (heroes, weapons, armor, rings, amulets, pets, runes,
skills, chapters) once real Archero 2 values are sourced. Nothing here yet — see the
root README's "Game data" section and the `GAME DATA PLACEHOLDER` docstrings in
`backend/app/domain/models/` for what's still illustrative rather than real.

Seed scripts, when added, should be idempotent (safe to re-run) and should populate
data purely through the SQLAlchemy models in `backend/app/domain/models/` — never via
raw SQL — so they stay valid as the schema evolves.
