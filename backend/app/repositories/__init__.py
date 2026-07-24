"""Data-access layer: thin, framework-agnostic functions over a Session.

Repositories depend only on `app.domain` (the ORM models) and SQLAlchemy
— never on FastAPI or Pydantic — so they're reusable from a script, the
optimizer engine (Module 3), or tests without booting the API. Anything
here that's more than "look this up" / "write this row" (e.g. rejecting
a duplicate display name) exists because it's a persistence-level
invariant, not a place for general business logic to accumulate — that
belongs in a service layer if/when Module 3 needs one.
"""
