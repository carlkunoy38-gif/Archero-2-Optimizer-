"""Tests for POST /api/v1/account."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Chapter


def test_create_account_success(client: TestClient) -> None:
    response = client.post("/api/v1/account", json={"display_name": "carl"})
    assert response.status_code == 201
    body = response.json()
    assert body["display_name"] == "carl"
    assert body["gold"] == 0
    assert body["gems"] == 0
    assert body["energy"] == 0
    assert body["combat_power"] == 0.0
    assert body["current_chapter_id"] is None
    assert "id" in body
    assert "created_at" in body


def test_create_account_with_resources_and_chapter(
    client: TestClient, db: Session
) -> None:
    chapter = Chapter(number=1, name="Whispering Forest")
    db.add(chapter)
    db.commit()

    response = client.post(
        "/api/v1/account",
        json={
            "display_name": "carl",
            "gold": 100,
            "gems": 5,
            "energy": 30,
            "combat_power": 1234.5,
            "current_chapter_id": chapter.id,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["gold"] == 100
    assert body["current_chapter_id"] == chapter.id


def test_create_account_duplicate_display_name_is_conflict(client: TestClient) -> None:
    client.post("/api/v1/account", json={"display_name": "carl"})
    response = client.post("/api/v1/account", json={"display_name": "carl"})
    assert response.status_code == 409
    assert "carl" in response.json()["detail"]


def test_create_account_nonexistent_chapter_is_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/account", json={"display_name": "carl", "current_chapter_id": 999}
    )
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


def test_create_account_rejects_negative_gold(client: TestClient) -> None:
    response = client.post(
        "/api/v1/account", json={"display_name": "carl", "gold": -1}
    )
    assert response.status_code == 422


def test_create_account_rejects_blank_display_name(client: TestClient) -> None:
    response = client.post("/api/v1/account", json={"display_name": ""})
    assert response.status_code == 422
