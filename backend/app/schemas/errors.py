"""Documents the shape every error response uses (see
`app/api/error_handlers.py`). Not used for validation — FastAPI's
exception handlers build the JSON body directly — this exists purely so
the shape shows up in the generated OpenAPI schema / Swagger UI instead
of being undocumented.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    type: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
