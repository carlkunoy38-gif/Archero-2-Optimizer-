"""Tests for POST /api/v1/optimizer/skills/advise."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import (
    Hero,
    HeroClass,
    Rarity,
    Skill,
    SkillType,
    UserAccount,
    UserHeroOwnership,
)


def test_advise_skills_happy_path(client: TestClient, db: Session) -> None:
    account = UserAccount(display_name="carl")
    hero_row = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=2000.0,
        base_defense=100.0,
        base_hp=600.0,
        base_attack_speed=1.0,
    )
    offensive_skill = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    defensive_skill = Skill(name="Iron Skin", skill_type=SkillType.DEFENSIVE, tier=3)
    db.add_all([account, hero_row, offensive_skill, defensive_skill])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=1, is_active=True))
    db.commit()

    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={
            "account_id": account.id,
            "candidate_skill_ids": [offensive_skill.id, defensive_skill.id],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_skill_id"] == offensive_skill.id
    assert len(body["ranking"]) == 2
    assert body["ranking"][0]["skill_id"] == offensive_skill.id
    assert body["ranking"][0]["score"] >= body["ranking"][1]["score"]
    assert body["ranking"][0]["reasons"]


def test_advise_skills_missing_account_is_not_found(client: TestClient, db: Session) -> None:
    skill = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE)
    db.add(skill)
    db.commit()

    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={"account_id": 999999, "candidate_skill_ids": [skill.id]},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_skills_missing_skill_is_not_found(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={"account_id": account.id, "candidate_skill_ids": [999999]},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_skills_empty_candidate_list_is_validation_error(
    client: TestClient, account: UserAccount
) -> None:
    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={"account_id": account.id, "candidate_skill_ids": []},
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"
