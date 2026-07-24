"""Tests for GET /api/v1/rings and GET /api/v1/rings/{ring_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Ring, StatType


def test_list_rings_empty(client: TestClient) -> None:
    response = client.get("/api/v1/rings")
    assert response.status_code == 200
    assert response.json() == []


def test_list_rings_returns_seeded_rows(client: TestClient, ring: Ring) -> None:
    response = client.get("/api/v1/rings")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_rings_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Ring(name="Common Ring", rarity=Rarity.COMMON, primary_stat=StatType.ATTACK),
            Ring(name="Epic Ring", rarity=Rarity.EPIC, primary_stat=StatType.ATTACK),
        ]
    )
    db.commit()

    response = client.get("/api/v1/rings", params={"rarity": "epic"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Epic Ring"}


def test_get_ring_detail(client: TestClient, ring: Ring) -> None:
    response = client.get(f"/api/v1/rings/{ring.id}")
    assert response.status_code == 200
    assert response.json()["id"] == ring.id


def test_get_ring_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/rings/999999")
    assert response.status_code == 404
