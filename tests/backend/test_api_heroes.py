"""Tests for GET /api/v1/heroes and GET /api/v1/heroes/{hero_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Hero, HeroClass, Rarity


def _make_hero(
    name: str, hero_class: HeroClass = HeroClass.WARRIOR, rarity: Rarity = Rarity.EPIC
) -> Hero:
    return Hero(name=name, hero_class=hero_class, rarity=rarity)


def test_list_heroes_empty(client: TestClient) -> None:
    response = client.get("/api/v1/heroes")
    assert response.status_code == 200
    assert response.json() == []


def test_list_heroes_returns_seeded_rows(client: TestClient, db: Session) -> None:
    db.add_all([_make_hero("Alpha"), _make_hero("Beta")])
    db.commit()

    response = client.get("/api/v1/heroes")
    assert response.status_code == 200
    names = {hero["name"] for hero in response.json()}
    assert names == {"Alpha", "Beta"}
    first = response.json()[0]
    assert first["hero_class"] == "warrior"
    assert first["rarity"] == "epic"
    assert "created_at" in first


def test_list_heroes_respects_limit_and_offset(client: TestClient, db: Session) -> None:
    db.add_all([_make_hero(f"Hero {i}") for i in range(5)])
    db.commit()

    response = client.get("/api/v1/heroes", params={"limit": 2, "offset": 3})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_heroes_rejects_invalid_limit(client: TestClient) -> None:
    response = client.get("/api/v1/heroes", params={"limit": 0})
    assert response.status_code == 422

    response = client.get("/api/v1/heroes", params={"limit": 500})
    assert response.status_code == 422


def test_list_heroes_filters_by_rarity(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            _make_hero("Common Hero", rarity=Rarity.COMMON),
            _make_hero("Legendary Hero", rarity=Rarity.LEGENDARY),
        ]
    )
    db.commit()

    response = client.get("/api/v1/heroes", params={"rarity": "legendary"})
    assert response.status_code == 200
    names = {hero["name"] for hero in response.json()}
    assert names == {"Legendary Hero"}


def test_list_heroes_filters_by_hero_class(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            _make_hero("Warrior Hero", hero_class=HeroClass.WARRIOR),
            _make_hero("Mage Hero", hero_class=HeroClass.MAGE),
        ]
    )
    db.commit()

    response = client.get("/api/v1/heroes", params={"hero_class": "mage"})
    assert response.status_code == 200
    names = {hero["name"] for hero in response.json()}
    assert names == {"Mage Hero"}


def test_get_hero_detail(client: TestClient, hero: Hero) -> None:
    response = client.get(f"/api/v1/heroes/{hero.id}")
    assert response.status_code == 200
    assert response.json()["id"] == hero.id
    assert response.json()["name"] == hero.name


def test_get_hero_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/heroes/999999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["type"] == "not_found"
