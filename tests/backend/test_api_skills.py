"""Tests for GET /api/v1/skills."""

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
