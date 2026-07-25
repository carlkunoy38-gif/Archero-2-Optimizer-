"""One-off catalog data seeding utilities.

Distinct from `app/services/`: these aren't business logic the API
needs at request time, just idempotent population of catalog rows from
real game data as it gets sourced — see `database/seeds/` for the
runnable entry points and `database/seeds/README.md` for how to run
them.
"""
