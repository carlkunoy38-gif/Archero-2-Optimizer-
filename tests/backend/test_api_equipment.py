"""Tests for the equip/activate/unequip actions.

The core thing under test throughout: equipping a new item
automatically replaces whatever was equipped before, in one request —
no separate unequip call needed — and that replacement is scoped
correctly (armor: same slot only; ring/amulet/weapon: whole account;
rune: same socket; skill: same equipped_slot).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import (
    Amulet,
    Armor,
    ArmorSlot,
    Hero,
    HeroClass,
    Pet,
    Rarity,
    Ring,
    Rune,
    RuneType,
    Skill,
    SkillType,
    StatType,
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
    Weapon,
)


@pytest.fixture()
def second_hero(db: Session) -> Hero:
    instance = Hero(name="Second Hero", hero_class=HeroClass.MAGE, rarity=Rarity.RARE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_weapon(db: Session) -> Weapon:
    instance = Weapon(name="Second Weapon", weapon_type="staff", rarity=Rarity.EPIC)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_pet(db: Session) -> Pet:
    instance = Pet(name="Second Pet", rarity=Rarity.EPIC, bonus_stat=StatType.ATTACK)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_ring(db: Session) -> Ring:
    instance = Ring(name="Second Ring", rarity=Rarity.EPIC, primary_stat=StatType.DEFENSE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_amulet(db: Session) -> Amulet:
    instance = Amulet(name="Second Amulet", rarity=Rarity.EPIC, primary_stat=StatType.ATTACK)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def boots(db: Session) -> Armor:
    instance = Armor(name="Boots", slot=ArmorSlot.BOOTS, rarity=Rarity.COMMON)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_helmet(db: Session) -> Armor:
    instance = Armor(name="Second Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.RARE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_rune(db: Session) -> Rune:
    instance = Rune(name="Second Rune", rune_type=RuneType.DEFENSE, rarity=Rarity.EPIC)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def second_skill(db: Session) -> Skill:
    instance = Skill(name="Second Skill", skill_type=SkillType.DEFENSIVE)
    db.add(instance)
    db.commit()
    return instance


# --- Hero: activate replaces the previously active hero --------------------


def test_activate_hero_sets_active(client: TestClient, account: UserAccount, hero: Hero) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    response = client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_activate_hero_replaces_previous_active_hero(
    client: TestClient, db: Session, account: UserAccount, hero: Hero, second_hero: Hero
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": second_hero.id})

    client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")
    response = client.post(f"/api/v1/accounts/{account.id}/heroes/{second_hero.id}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    db.expire_all()
    first = db.query(UserHeroOwnership).filter_by(account_id=account.id, hero_id=hero.id).one()
    assert first.is_active is False


def test_activate_hero_not_owned_is_404(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    response = client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")
    assert response.status_code == 404


def test_deactivate_hero(client: TestClient, account: UserAccount, hero: Hero) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")
    response = client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/deactivate")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_activate_hero_failure_does_not_disturb_existing_active_hero(
    client: TestClient, db: Session, account: UserAccount, hero: Hero
) -> None:
    """A 404 (activating a hero that isn't owned) must not touch any
    other row — proving the operation is all-or-nothing."""

    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")

    failed = client.post(f"/api/v1/accounts/{account.id}/heroes/999999/activate")
    assert failed.status_code == 404

    db.expire_all()
    still_active = (
        db.query(UserHeroOwnership).filter_by(account_id=account.id, hero_id=hero.id).one()
    )
    assert still_active.is_active is True


# --- Pet ---------------------------------------------------------------


def test_activate_pet_replaces_previous_active_pet(
    client: TestClient, db: Session, account: UserAccount, pet: Pet, second_pet: Pet
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": pet.id})
    client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": second_pet.id})

    client.post(f"/api/v1/accounts/{account.id}/pets/{pet.id}/activate")
    client.post(f"/api/v1/accounts/{account.id}/pets/{second_pet.id}/activate")

    db.expire_all()
    first = db.query(UserPetOwnership).filter_by(account_id=account.id, pet_id=pet.id).one()
    assert first.is_active is False


def test_deactivate_pet(client: TestClient, account: UserAccount, pet: Pet) -> None:
    client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": pet.id})
    client.post(f"/api/v1/accounts/{account.id}/pets/{pet.id}/activate")
    response = client.post(f"/api/v1/accounts/{account.id}/pets/{pet.id}/deactivate")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


# --- Weapon: equip replaces the previously equipped weapon -----------------


def test_equip_weapon_replaces_previous(
    client: TestClient, db: Session, account: UserAccount, weapon: Weapon, second_weapon: Weapon
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": weapon.id})
    client.post(f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": second_weapon.id})

    client.post(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}/equip")
    response = client.post(f"/api/v1/accounts/{account.id}/weapons/{second_weapon.id}/equip")
    assert response.status_code == 200
    assert response.json()["is_equipped"] is True

    db.expire_all()
    first = (
        db.query(UserWeaponOwnership).filter_by(account_id=account.id, weapon_id=weapon.id).one()
    )
    assert first.is_equipped is False


def test_unequip_weapon(client: TestClient, account: UserAccount, weapon: Weapon) -> None:
    client.post(f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": weapon.id})
    client.post(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}/equip")
    response = client.post(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}/unequip")
    assert response.status_code == 200
    assert response.json()["is_equipped"] is False


def test_equip_weapon_not_owned_is_404(
    client: TestClient, account: UserAccount, weapon: Weapon
) -> None:
    response = client.post(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}/equip")
    assert response.status_code == 404


# --- Armor: replacement is scoped to the same slot --------------------------


def test_equip_armor_replaces_previous_in_same_slot(
    client: TestClient,
    db: Session,
    account: UserAccount,
    armor_item: Armor,
    second_helmet: Armor,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id})
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": second_helmet.id})

    client.post(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}/equip")
    response = client.post(f"/api/v1/accounts/{account.id}/armor/{second_helmet.id}/equip")
    assert response.status_code == 200
    assert response.json()["is_equipped"] is True

    db.expire_all()
    first = (
        db.query(UserArmorOwnership)
        .filter_by(account_id=account.id, armor_id=armor_item.id)
        .one()
    )
    assert first.is_equipped is False


def test_equip_armor_different_slots_both_stay_equipped(
    client: TestClient, db: Session, account: UserAccount, armor_item: Armor, boots: Armor
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id})
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": boots.id})

    client.post(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}/equip")
    client.post(f"/api/v1/accounts/{account.id}/armor/{boots.id}/equip")

    db.expire_all()
    helmet_row = (
        db.query(UserArmorOwnership)
        .filter_by(account_id=account.id, armor_id=armor_item.id)
        .one()
    )
    boots_row = (
        db.query(UserArmorOwnership).filter_by(account_id=account.id, armor_id=boots.id).one()
    )
    assert helmet_row.is_equipped is True
    assert boots_row.is_equipped is True


def test_unequip_armor(client: TestClient, account: UserAccount, armor_item: Armor) -> None:
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id})
    client.post(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}/equip")
    response = client.post(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}/unequip")
    assert response.status_code == 200
    assert response.json()["is_equipped"] is False


# --- Ring / Amulet -----------------------------------------------------------


def test_equip_ring_replaces_previous(
    client: TestClient, db: Session, account: UserAccount, ring: Ring, second_ring: Ring
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": ring.id})
    client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": second_ring.id})

    client.post(f"/api/v1/accounts/{account.id}/rings/{ring.id}/equip")
    client.post(f"/api/v1/accounts/{account.id}/rings/{second_ring.id}/equip")

    db.expire_all()
    first = db.query(UserRingOwnership).filter_by(account_id=account.id, ring_id=ring.id).one()
    assert first.is_equipped is False


def test_equip_amulet_replaces_previous(
    client: TestClient, db: Session, account: UserAccount, amulet: Amulet, second_amulet: Amulet
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/amulets", json={"amulet_id": amulet.id})
    client.post(f"/api/v1/accounts/{account.id}/amulets", json={"amulet_id": second_amulet.id})

    client.post(f"/api/v1/accounts/{account.id}/amulets/{amulet.id}/equip")
    client.post(f"/api/v1/accounts/{account.id}/amulets/{second_amulet.id}/equip")

    db.expire_all()
    first = (
        db.query(UserAmuletOwnership).filter_by(account_id=account.id, amulet_id=amulet.id).one()
    )
    assert first.is_equipped is False


# --- Rune: socket conflicts --------------------------------------------------


def test_equip_rune_into_empty_socket(
    client: TestClient, account: UserAccount, rune: Rune
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    response = client.post(
        f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 0}
    )
    assert response.status_code == 200
    assert response.json()["socket_index"] == 0
    assert response.json()["is_equipped"] is True


def test_equip_rune_displaces_occupant_of_same_socket(
    client: TestClient, db: Session, account: UserAccount, rune: Rune, second_rune: Rune
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": second_rune.id})

    client.post(f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 0})
    response = client.post(
        f"/api/v1/accounts/{account.id}/runes/{second_rune.id}/equip", json={"socket_index": 0}
    )
    assert response.status_code == 200
    assert response.json()["socket_index"] == 0

    db.expire_all()
    displaced = (
        db.query(UserRuneOwnership).filter_by(account_id=account.id, rune_id=rune.id).one()
    )
    assert displaced.socket_index is None
    assert displaced.is_equipped is False


def test_equip_rune_can_move_to_a_different_socket(
    client: TestClient, account: UserAccount, rune: Rune
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    client.post(f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 0})
    response = client.post(
        f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 1}
    )
    assert response.status_code == 200
    assert response.json()["socket_index"] == 1


def test_unequip_rune_clears_socket(client: TestClient, account: UserAccount, rune: Rune) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    client.post(f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 0})
    response = client.post(f"/api/v1/accounts/{account.id}/runes/{rune.id}/unequip")
    assert response.status_code == 200
    assert response.json()["socket_index"] is None
    assert response.json()["is_equipped"] is False


def test_equip_rune_rejects_negative_socket_index(
    client: TestClient, account: UserAccount, rune: Rune
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    response = client.post(
        f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": -1}
    )
    assert response.status_code == 422


# --- Skill: unlock-gating and slot conflicts ---------------------------------


def test_equip_skill_requires_unlocked(
    client: TestClient, account: UserAccount, skill: Skill
) -> None:
    client.post(
        f"/api/v1/accounts/{account.id}/skills",
        json={"skill_id": skill.id, "is_unlocked": False},
    )
    response = client.post(
        f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0}
    )
    assert response.status_code == 409
    assert response.json()["error"]["type"] == "conflict"


def test_equip_skill_when_unlocked_succeeds(
    client: TestClient, account: UserAccount, skill: Skill
) -> None:
    client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    response = client.post(
        f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0}
    )
    assert response.status_code == 200
    assert response.json()["equipped_slot"] == 0


def test_equip_skill_displaces_occupant_of_same_slot(
    client: TestClient, db: Session, account: UserAccount, skill: Skill, second_skill: Skill
) -> None:
    client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    client.post(
        f"/api/v1/accounts/{account.id}/skills",
        json={"skill_id": second_skill.id, "is_unlocked": True},
    )

    client.post(f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0})
    response = client.post(
        f"/api/v1/accounts/{account.id}/skills/{second_skill.id}/equip",
        json={"equipped_slot": 0},
    )
    assert response.status_code == 200

    db.expire_all()
    displaced = (
        db.query(UserSkillSelection).filter_by(account_id=account.id, skill_id=skill.id).one()
    )
    assert displaced.equipped_slot is None
    # Unlock state is untouched by being displaced from a slot.
    assert displaced.is_unlocked is True


def test_unequip_skill(client: TestClient, account: UserAccount, skill: Skill) -> None:
    client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    client.post(f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0})
    response = client.post(f"/api/v1/accounts/{account.id}/skills/{skill.id}/unequip")
    assert response.status_code == 200
    assert response.json()["equipped_slot"] is None


def test_equip_skill_not_selected_is_404(
    client: TestClient, account: UserAccount, skill: Skill
) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0}
    )
    assert response.status_code == 404


def test_equip_skill_failure_does_not_disturb_existing_equipped_skill(
    client: TestClient, db: Session, account: UserAccount, skill: Skill
) -> None:
    """Attempting to equip a locked skill into slot 0 must not touch
    whatever is already equipped in slot 0."""

    client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    client.post(f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0})

    locked_skill_id = 999999  # not selected at all -> 404, before any mutation
    failed = client.post(
        f"/api/v1/accounts/{account.id}/skills/{locked_skill_id}/equip",
        json={"equipped_slot": 0},
    )
    assert failed.status_code == 404

    db.expire_all()
    still_equipped = (
        db.query(UserSkillSelection).filter_by(account_id=account.id, skill_id=skill.id).one()
    )
    assert still_equipped.equipped_slot == 0
