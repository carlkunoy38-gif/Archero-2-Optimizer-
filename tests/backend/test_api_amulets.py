"""Tests for GET /api/v1/amulets and GET /api/v1/amulets/{amulet_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Amulet, Rarity, StatType


def test_list_amulets_empty(client: TestClient) -> None:
    response = client.get("/api/v1/amulets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_amulets_returns_seeded_rows(client: TestClient, amulet: Amulet) -> None:
    response = client.get("/api/v1/amulets")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_amulets_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Amulet(name="Common Amulet", rarity=Rarity.COMMON, primary_stat=StatType.DEFENSE),
            Amulet(name="Mythic Amulet", rarity=Rarity.MYTHIC, primary_stat=StatType.DEFENSE),
        ]
    )
    db.commit()

    response = client.get("/api/v1/amulets", params={"rarity": "mythic"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Mythic Amulet"}


def test_get_amulet_detail(client: TestClient, amulet: Amulet) -> None:
    response = client.get(f"/api/v1/amulets/{amulet.id}")
    assert response.status_code == 200
    assert response.json()["id"] == amulet.id


def test_get_amulet_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/amulets/999999")
    assert response.status_code == 404
