"""Tests for GET /api/v1/weapons."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Weapon


def test_list_weapons_empty(client: TestClient) -> None:
    response = client.get("/api/v1/weapons")
    assert response.status_code == 200
    assert response.json() == []


def test_list_weapons_returns_seeded_rows(client: TestClient, db: Session) -> None:
    db.add(Weapon(name="Sample Bow", weapon_type="bow", rarity=Rarity.RARE, base_damage=25.0))
    db.commit()

    response = client.get("/api/v1/weapons")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Sample Bow"
    assert body[0]["weapon_type"] == "bow"
    assert body[0]["rarity"] == "rare"


def test_list_weapons_rejects_invalid_offset(client: TestClient) -> None:
    response = client.get("/api/v1/weapons", params={"offset": -1})
    assert response.status_code == 422
