"""Business-logic layer.

A service function is where "does this request make sense given the
current state of the data" gets decided: does the referenced account
exist, is this display name already taken, does equipping this weapon
need to un-equip another one first. Repositories underneath stay pure
data access; routes above stay a translation from HTTP into a service
call and back.

Every service function that fails does so by raising `NotFoundError` or
`ConflictError` from `app.core.exceptions` — never `fastapi.HTTPException`
— so this layer has no FastAPI dependency and stays callable from a
script, a future CLI, or the optimizer engine.
"""
