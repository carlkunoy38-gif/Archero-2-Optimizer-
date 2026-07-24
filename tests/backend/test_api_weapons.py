"""Tests for GET /api/v1/weapons and GET /api/v1/weapons/{weapon_id}."""

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


def test_list_weapons_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Weapon(name="Common Bow", weapon_type="bow", rarity=Rarity.COMMON),
            Weapon(name="Epic Staff", weapon_type="staff", rarity=Rarity.EPIC),
        ]
    )
    db.commit()

    response = client.get("/api/v1/weapons", params={"rarity": "epic"})
    assert response.status_code == 200
    names = {weapon["name"] for weapon in response.json()}
    assert names == {"Epic Staff"}


def test_list_weapons_filters_by_weapon_type(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Weapon(name="Bow A", weapon_type="bow", rarity=Rarity.RARE),
            Weapon(name="Staff A", weapon_type="staff", rarity=Rarity.RARE),
        ]
    )
    db.commit()

    response = client.get("/api/v1/weapons", params={"weapon_type": "staff"})
    assert response.status_code == 200
    names = {weapon["name"] for weapon in response.json()}
    assert names == {"Staff A"}


def test_get_weapon_detail(client: TestClient, weapon: Weapon) -> None:
    response = client.get(f"/api/v1/weapons/{weapon.id}")
    assert response.status_code == 200
    assert response.json()["id"] == weapon.id


def test_get_weapon_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/weapons/999999")
    assert response.status_code == 404
