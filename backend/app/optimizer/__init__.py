"""The optimizer engine: the project's central decision-making
subsystem, and the reason Archero 2 Optimizer is more than a database
with an API attached.

This package never automates gameplay, sends input to the game, or
reads/modifies game state — it only reads what's already in the
database (via `app.repositories`) and returns a recommendation with
reasoning. The player always decides and always plays; the engine only
advises.

Why a top-level package and not another module under `app/services/`:
everything already in `services/` is CRUD-shaped — validate a request,
mutate the database, return the result. The optimizer engine is a
different *kind* of logic: read-only analysis over a snapshot of a
build, with no side effects and no request to validate. Keeping it
separate also matches how it's meant to grow — every advisor listed in
the brief (Gear, Farm, Upgrade, Rune, Resource) will live under
`app/optimizer/advisors/`, sharing the same `BuildContext` and the same
scoring primitives in `app/optimizer/engine.py`, rather than each
service file reinventing "how strong is this build offensively."

Layering within this package, so a future advisor knows where new code
goes:

    weights.py    — every tunable number, in one place (see its docstring)
    context.py    — BuildContext: a pure data snapshot of one account's
                    current build, plus the function that assembles one
                    from a `UserAccount` ORM object
    engine.py     — shared scoring primitives, functions of a
                    BuildContext only (offense_score, defense_score, ...)
    results.py    — ScoredOption / AdvisorResult: the generic shape
                    every advisor reports a recommendation in
    advisors/     — one module per advisor; each exposes a pure
                    `advise(context, candidates)` function (no I/O) and
                    a `advise_for_account(db, account_id, ...)` wrapper
                    that loads the account and delegates to it

`context.py`, `engine.py`, `weights.py`, and `results.py` depend on
nothing but `app.domain` (for ORM types and enums) — no database
session, no FastAPI. That's deliberate: the scoring engine itself only
needs a `BuildContext` value object, so it's equally usable from a web
request, a future CLI, a batch job, or (per the brief's stated future)
a screenshot-analysis pipeline that produces a `BuildContext` some
other way entirely.
"""
