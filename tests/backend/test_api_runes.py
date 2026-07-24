"""Tests for GET /api/v1/runes and GET /api/v1/runes/{rune_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Rarity, Rune, RuneType


def test_list_runes_empty(client: TestClient) -> None:
    response = client.get("/api/v1/runes")
    assert response.status_code == 200
    assert response.json() == []


def test_list_runes_returns_seeded_rows(client: TestClient, rune: Rune) -> None:
    response = client.get("/api/v1/runes")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_runes_filters_by_rune_type(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Rune(name="Offense Rune", rune_type=RuneType.OFFENSE, rarity=Rarity.RARE),
            Rune(name="Defense Rune", rune_type=RuneType.DEFENSE, rarity=Rarity.RARE),
        ]
    )
    db.commit()

    response = client.get("/api/v1/runes", params={"rune_type": "defense"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Defense Rune"}


def test_list_runes_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Rune(name="Common Rune", rune_type=RuneType.UTILITY, rarity=Rarity.COMMON),
            Rune(name="Epic Rune", rune_type=RuneType.UTILITY, rarity=Rarity.EPIC),
        ]
    )
    db.commit()

    response = client.get("/api/v1/runes", params={"rarity": "epic"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Epic Rune"}


def test_get_rune_detail(client: TestClient, rune: Rune) -> None:
    response = client.get(f"/api/v1/runes/{rune.id}")
    assert response.status_code == 200
    assert response.json()["id"] == rune.id


def test_get_rune_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/runes/999999")
    assert response.status_code == 404
