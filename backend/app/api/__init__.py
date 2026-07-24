"""HTTP API layer: FastAPI routers and request/response wiring.

Depends on `app.schemas` and `app.repositories`, never the other way
around, and never reaches into `app.domain` directly for anything but
type hints — a route handler's job is to validate input, call a
repository function, and translate the result (or a repository error)
into an HTTP response.
"""
