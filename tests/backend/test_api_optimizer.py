"""Tests for the optimizer advisor endpoints: POST
/api/v1/optimizer/skills/advise, /gear/advise, /upgrade/advise, and
/chapters/advise.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import (
    Armor,
    ArmorSlot,
    Chapter,
    EffectType,
    Hero,
    HeroClass,
    Rarity,
    Skill,
    SkillEffect,
    SkillType,
    UserAccount,
    UserArmorOwnership,
    UserChapterProgress,
    UserHeroOwnership,
    UserWeaponOwnership,
    Weapon,
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


# --- POST /optimizer/gear/advise ----------------------------------------


def test_advise_gear_happy_path_ranks_owned_weapons(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    strong = Weapon(
        name="Strong Bow", weapon_type="bow", rarity=Rarity.LEGENDARY, base_damage=100.0
    )
    weak = Weapon(name="Weak Dagger", weapon_type="dagger", rarity=Rarity.COMMON, base_damage=10.0)
    db.add_all([strong, weak])
    db.commit()
    db.add(
        UserWeaponOwnership(account_id=account.id, weapon_id=strong.id, level=1, is_equipped=False)
    )
    db.add(UserWeaponOwnership(account_id=account.id, weapon_id=weak.id, level=1, is_equipped=True))
    db.commit()

    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": account.id, "category": "weapon"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_catalog_id"] == strong.id
    assert len(body["ranking"]) == 2
    assert body["ranking"][0]["reasons"]
    assert body["ranking"][0]["summary"]


def test_advise_gear_armor_without_slot_is_validation_error(
    client: TestClient, account: UserAccount
) -> None:
    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": account.id, "category": "armor"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_advise_gear_armor_with_slot_scopes_the_ranking(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    helmet = Armor(name="Good Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.EPIC, base_defense=50.0)
    db.add(helmet)
    db.commit()
    db.add(
        UserArmorOwnership(
            account_id=account.id, armor_id=helmet.id, armor=helmet, level=1, is_equipped=True
        )
    )
    db.commit()

    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": account.id, "category": "armor", "armor_slot": "helmet"},
    )

    assert response.status_code == 200
    assert response.json()["recommended_catalog_id"] == helmet.id


def test_advise_gear_missing_account_is_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": 999999, "category": "weapon"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_gear_nothing_owned_is_not_found(client: TestClient, account: UserAccount) -> None:
    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": account.id, "category": "ring"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_gear_unknown_objective_is_not_found(
    client: TestClient, db: Session, account: UserAccount, weapon: Weapon
) -> None:
    db.add(
        UserWeaponOwnership(account_id=account.id, weapon_id=weapon.id, level=1, is_equipped=True)
    )
    db.commit()

    response = client.post(
        "/api/v1/optimizer/gear/advise",
        json={"account_id": account.id, "category": "weapon", "objective": "nonsense"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


# --- POST /optimizer/upgrade/advise -------------------------------------


def test_advise_upgrade_happy_path_recommends_the_best_affordable_upgrade(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    account.gold = 1000
    hero_row = Hero(
        name="Hero",
        hero_class=HeroClass.WARRIOR,
        rarity=Rarity.EPIC,
        base_attack=100.0,
        base_defense=10.0,
        base_hp=200.0,
        base_attack_speed=0.0,
    )
    db.add(hero_row)
    db.commit()
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero_row.id, level=3, is_active=True))
    db.commit()

    response = client.post("/api/v1/optimizer/upgrade/advise", json={"account_id": account.id})

    assert response.status_code == 200
    body = response.json()
    assert body["recommended"] == {
        "category": "hero",
        "ownership_id": body["ranking"][0]["ownership_id"],
        "catalog_id": hero_row.id,
    }
    assert body["ranking"][0]["category"] == "hero"
    assert body["ranking"][0]["ownership_id"]
    assert body["ranking"][0]["reasons"]
    assert body["ranking"][0]["summary"]


def test_advise_upgrade_missing_account_is_not_found(client: TestClient) -> None:
    response = client.post("/api/v1/optimizer/upgrade/advise", json={"account_id": 999999})

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_upgrade_nothing_affordable_is_not_found(
    client: TestClient, db: Session, account: UserAccount, hero: Hero
) -> None:
    account.gold = 0
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=1, is_active=True))
    db.commit()

    response = client.post("/api/v1/optimizer/upgrade/advise", json={"account_id": account.id})

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_upgrade_unknown_objective_is_not_found(
    client: TestClient, db: Session, account: UserAccount, hero: Hero
) -> None:
    account.gold = 1000
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=1, is_active=True))
    db.commit()

    response = client.post(
        "/api/v1/optimizer/upgrade/advise",
        json={"account_id": account.id, "objective": "nonsense"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


# --- POST /optimizer/chapters/advise -------------------------------------


def test_advise_chapters_happy_path_recommends_a_chapter(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    account.combat_power = 1000.0
    near = Chapter(number=1, name="Easy Meadow", recommended_combat_power=400.0, energy_cost=3)
    far = Chapter(number=2, name="Far Ridge", recommended_combat_power=950.0, energy_cost=10)
    db.add_all([near, far])
    db.commit()
    # Chapter 2 is only unlocked once chapter 1 is cleared.
    db.add(UserChapterProgress(account_id=account.id, chapter_id=near.id, cleared=True))
    db.commit()

    response = client.post(
        "/api/v1/optimizer/chapters/advise",
        json={"account_id": account.id, "objective": "balanced"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_chapter_id"] == far.id
    assert len(body["ranking"]) == 2
    assert body["ranking"][0]["reasons"]
    assert body["ranking"][0]["summary"]


def test_advise_chapters_farm_mode_prefers_cheap_safe_chapter(
    client: TestClient, db: Session, account: UserAccount
) -> None:
    account.combat_power = 1000.0
    cheap = Chapter(number=1, name="Easy Meadow", recommended_combat_power=400.0, energy_cost=3)
    costly = Chapter(number=2, name="Hard Peak", recommended_combat_power=900.0, energy_cost=30)
    db.add_all([cheap, costly])
    db.commit()

    response = client.post(
        "/api/v1/optimizer/chapters/advise",
        json={"account_id": account.id, "objective": "farm"},
    )

    assert response.status_code == 200
    assert response.json()["recommended_chapter_id"] == cheap.id


def test_advise_chapters_missing_account_is_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/optimizer/chapters/advise", json={"account_id": 999999}
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_chapters_empty_catalog_is_not_found(
    client: TestClient, account: UserAccount
) -> None:
    response = client.post(
        "/api/v1/optimizer/chapters/advise", json={"account_id": account.id}
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_advise_chapters_unknown_objective_is_not_found(
    client: TestClient, account: UserAccount, chapter: Chapter
) -> None:
    response = client.post(
        "/api/v1/optimizer/chapters/advise",
        json={"account_id": account.id, "objective": "nonsense"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"
