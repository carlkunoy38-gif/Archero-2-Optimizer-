"""Tests for GET /api/v1/armor and GET /api/v1/armor/{armor_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Armor, ArmorSlot, Rarity


def test_list_armor_empty(client: TestClient) -> None:
    response = client.get("/api/v1/armor")
    assert response.status_code == 200
    assert response.json() == []


def test_list_armor_returns_seeded_rows(client: TestClient, armor_item: Armor) -> None:
    response = client.get("/api/v1/armor")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slot"] == "helmet"


def test_list_armor_filters_by_slot(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Armor(name="Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON),
            Armor(name="Boots", slot=ArmorSlot.BOOTS, rarity=Rarity.COMMON),
        ]
    )
    db.commit()

    response = client.get("/api/v1/armor", params={"slot": "boots"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Boots"}


def test_list_armor_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Armor(name="Common Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON),
            Armor(name="Rare Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.RARE),
        ]
    )
    db.commit()

    response = client.get("/api/v1/armor", params={"rarity": "rare"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Rare Helmet"}


def test_get_armor_detail(client: TestClient, armor_item: Armor) -> None:
    response = client.get(f"/api/v1/armor/{armor_item.id}")
    assert response.status_code == 200
    assert response.json()["slot"] == "helmet"


def test_get_armor_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/armor/999999")
    assert response.status_code == 404
