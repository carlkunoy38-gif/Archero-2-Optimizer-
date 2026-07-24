"""Tests for POST /api/v1/optimizer/skills/advise."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import (
    EffectType,
    Hero,
    HeroClass,
    Rarity,
    Skill,
    SkillEffect,
    SkillType,
    UserAccount,
    UserHeroOwnership,
)


def _seed_account_and_skills(db: Session) -> tuple[UserAccount, Skill, Skill]:
    account = UserAccount(display_name="carl")
    hero_row = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=500.0,
        base_defense=50.0,
        base_hp=800.0,
        base_attack_speed=0.5,
    )
    multishot = Skill(name="Multishot", skill_type=SkillType.OFFENSIVE, tier=3)
    multishot.effects = [SkillEffect(effect_type=EffectType.PROJECTILE_COUNT, value=1.0)]
    attack_up = Skill(name="Attack Up", skill_type=SkillType.OFFENSIVE, tier=3)
    attack_up.effects = [SkillEffect(effect_type=EffectType.ATTACK_SPEED_MULTIPLIER, value=0.15)]
    db.add_all([account, hero_row, multishot, attack_up])
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=1, is_active=True))
    db.commit()
    return account, multishot, attack_up


def test_advise_skills_happy_path_defaults_to_balanced_objective(
    client: TestClient, db: Session
) -> None:
    account, multishot, attack_up = _seed_account_and_skills(db)

    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={
            "account_id": account.id,
            "candidate_skill_ids": [multishot.id, attack_up.id],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_skill_id"] == attack_up.id
    assert len(body["ranking"]) == 2
    assert body["ranking"][0]["skill_id"] == attack_up.id
    assert body["ranking"][0]["score"] >= body["ranking"][1]["score"]
    assert body["ranking"][0]["reasons"]
    assert body["ranking"][0]["summary"]


def test_advise_skills_respects_objective_query_field(client: TestClient, db: Session) -> None:
    account, multishot, attack_up = _seed_account_and_skills(db)

    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={
            "account_id": account.id,
            "candidate_skill_ids": [multishot.id, attack_up.id],
            "objective": "farm",
        },
    )

    assert response.status_code == 200
    assert response.json()["recommended_skill_id"] == multishot.id


def test_advise_skills_unknown_objective_is_not_found(client: TestClient, db: Session) -> None:
    account, multishot, _attack_up = _seed_account_and_skills(db)

    response = client.post(
        "/api/v1/optimizer/skills/advise",
        json={
            "account_id": account.id,
            "candidate_skill_ids": [multishot.id],
            "objective": "nonsense",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


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
