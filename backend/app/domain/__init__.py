"""Domain layer: ORM entities that model Archero 2 game concepts.

This package has no dependency on FastAPI, Pydantic schemas, or the API
layer — only on SQLAlchemy — so the domain model can be reused by the
scoring engine, CLI tools, or tests without pulling in the web framework.
"""
