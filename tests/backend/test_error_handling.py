"""Every error response shares one envelope shape:
{"error": {"type": ..., "message": ..., "details": ...}} — regardless of
whether it came from a domain exception, Pydantic validation, an
unmatched route, or a genuinely unexpected bug. See
`app/api/error_handlers.py`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import get_db
from app.domain.models import UserAccount
from app.main import create_app
from app.services import catalog_service


def test_not_found_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/heroes/999999")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["type"] == "not_found"
    assert isinstance(body["error"]["message"], str)


def test_conflict_error_envelope(client: TestClient) -> None:
    client.post("/api/v1/accounts", json={"display_name": "carl"})
    response = client.post("/api/v1/accounts", json={"display_name": "carl"})
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["type"] == "conflict"


def test_validation_error_envelope_includes_field_details(client: TestClient) -> None:
    response = client.post("/api/v1/accounts", json={"display_name": "carl", "gold": -1})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["type"] == "validation_error"
    assert isinstance(body["error"]["details"], list)
    assert any("gold" in str(item.get("loc")) for item in body["error"]["details"])


def test_unmatched_route_returns_http_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/this-route-does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["type"] == "http_error"


def test_unexpected_exception_returns_500_envelope_without_leaking_details(
    db: Session, account: UserAccount, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(db: object, hero_id: int) -> UserAccount:
        raise RuntimeError("boom: raw internal detail that must not leak")

    monkeypatch.setattr(catalog_service, "get_hero", _boom)

    # Two things the shared `client` fixture can't give us here:
    # (1) debug=True (its default, and every other test's) makes
    #     Starlette's ServerErrorMiddleware render its own HTML/text
    #     debug traceback page instead of invoking our registered
    #     Exception handler at all — regardless of registration — so
    #     verifying the *production* JSON envelope needs a debug=False
    #     app.
    # (2) raise_server_exceptions=True (also the default) re-raises even
    #     a *handled* exception into the test process for debuggability,
    #     which is what every other test wants but not this one.
    non_debug_app = create_app(Settings(_env_file=None, debug=False))  # type: ignore[call-arg]

    def _override_get_db() -> object:
        yield db

    non_debug_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(non_debug_app, raise_server_exceptions=False) as non_debug_client:
        response = non_debug_client.get("/api/v1/heroes/1")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["type"] == "internal_error"
    assert "boom" not in body["error"]["message"]
    assert "raw internal detail" not in response.text
