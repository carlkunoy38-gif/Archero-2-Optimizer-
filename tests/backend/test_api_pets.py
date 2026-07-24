"""Tests for GET /api/v1/pets and GET /api/v1/pets/{pet_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Pet, Rarity, StatType


def test_list_pets_empty(client: TestClient) -> None:
    response = client.get("/api/v1/pets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_pets_returns_seeded_rows(client: TestClient, pet: Pet) -> None:
    response = client.get("/api/v1/pets")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_pets_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Pet(name="Common Pet", rarity=Rarity.COMMON, bonus_stat=StatType.HEALTH),
            Pet(name="Legendary Pet", rarity=Rarity.LEGENDARY, bonus_stat=StatType.HEALTH),
        ]
    )
    db.commit()

    response = client.get("/api/v1/pets", params={"rarity": "legendary"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Legendary Pet"}


def test_get_pet_detail(client: TestClient, pet: Pet) -> None:
    response = client.get(f"/api/v1/pets/{pet.id}")
    assert response.status_code == 200
    assert response.json()["id"] == pet.id


def test_get_pet_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/pets/999999")
    assert response.status_code == 404
