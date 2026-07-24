"""Tests for GET /api/v1/skills and GET /api/v1/skills/{skill_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Skill, SkillType


def test_list_skills_empty(client: TestClient) -> None:
    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    assert response.json() == []


def test_list_skills_returns_seeded_rows(client: TestClient, db: Session) -> None:
    db.add(Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=2))
    db.commit()

    response = client.get("/api/v1/skills")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Multishot"
    assert body[0]["skill_type"] == "offensive"
    assert body[0]["tier"] == 2


def test_list_skills_filters_by_skill_type(client: TestClient, db: Session) -> None:
    db.add_all(
        [
            Skill(name="Offense Skill", skill_type=SkillType.OFFENSIVE),
            Skill(name="Movement Skill", skill_type=SkillType.MOVEMENT),
        ]
    )
    db.commit()

    response = client.get("/api/v1/skills", params={"skill_type": "movement"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Movement Skill"}


def test_get_skill_detail(client: TestClient, skill: Skill) -> None:
    response = client.get(f"/api/v1/skills/{skill.id}")
    assert response.status_code == 200
    assert response.json()["id"] == skill.id


def test_get_skill_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/skills/999999")
    assert response.status_code == 404
