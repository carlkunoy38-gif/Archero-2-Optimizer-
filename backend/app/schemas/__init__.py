"""Pydantic request/response schemas for the API layer.

These are deliberately separate from the domain (ORM) models: a schema
describes what crosses the HTTP boundary, while a domain model describes
what's persisted. They happen to overlap heavily for the simple
read-only catalog endpoints in this module, but keeping them distinct
means a field can be added to one without silently changing the other.
"""
