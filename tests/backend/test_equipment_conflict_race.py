"""Simulates the concurrent-equip race that `app/services/equipment_service.py`
now guards against: two requests each pass their own "clear whatever
else is equipped" step before either commits, so both end up trying to
set `is_equipped`/`is_active` (or claim the same rune socket / skill
slot) True for the same account at once. Module 1's partial unique
indexes are what actually prevent the corrupted end state — one of the
two commits fails with `IntegrityError` — and the fix under test here
is that failure now surfacing as a clean 409 `conflict`, not an
unhandled 500.

True thread-level concurrency is hard to reproduce deterministically in
a synchronous test, so each test here reproduces the *effect* directly:
monkeypatch the relevant `clear_*` repository call to a no-op (standing
in for "a concurrent request's clear already ran and this request's own
clear step never got the chance to see it"), pre-arm a conflicting
row, and confirm the second equip/activate call gets a 409 instead of
a 500.
"""

from __future__ import annotations

import httpx
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
    Weapon,
)
from app.repositories import ownership as ownership_repo


@pytest.fixture()
def second_hero(db: Session) -> Hero:
    instance = Hero(name="Second Hero", hero_class=HeroClass.MAGE, rarity=Rarity.RARE)
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
def second_weapon(db: Session) -> Weapon:
    instance = Weapon(name="Second Weapon", weapon_type="staff", rarity=Rarity.EPIC)
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


def _assert_conflict_not_server_error(response: httpx.Response) -> None:
    assert response.status_code == 409, (
        f"expected 409 conflict, got {response.status_code}: {response.text}"
    )
    assert response.json()["error"]["type"] == "conflict"


def test_activate_hero_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    hero: Hero,
    second_hero: Hero,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": second_hero.id})
    client.post(f"/api/v1/accounts/{account.id}/heroes/{hero.id}/activate")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/heroes/{second_hero.id}/activate")
    _assert_conflict_not_server_error(response)


def test_activate_pet_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    pet: Pet,
    second_pet: Pet,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": pet.id})
    client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": second_pet.id})
    client.post(f"/api/v1/accounts/{account.id}/pets/{pet.id}/activate")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/pets/{second_pet.id}/activate")
    _assert_conflict_not_server_error(response)


def test_equip_weapon_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    weapon: Weapon,
    second_weapon: Weapon,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": weapon.id})
    client.post(f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": second_weapon.id})
    client.post(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}/equip")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/weapons/{second_weapon.id}/equip")
    _assert_conflict_not_server_error(response)


def test_equip_armor_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    armor_item: Armor,
    second_helmet: Armor,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id})
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": second_helmet.id})
    client.post(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}/equip")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/armor/{second_helmet.id}/equip")
    _assert_conflict_not_server_error(response)


def test_equip_ring_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    ring: Ring,
    second_ring: Ring,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": ring.id})
    client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": second_ring.id})
    client.post(f"/api/v1/accounts/{account.id}/rings/{ring.id}/equip")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/rings/{second_ring.id}/equip")
    _assert_conflict_not_server_error(response)


def test_equip_amulet_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    amulet: Amulet,
    second_amulet: Amulet,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/amulets", json={"amulet_id": amulet.id})
    client.post(f"/api/v1/accounts/{account.id}/amulets", json={"amulet_id": second_amulet.id})
    client.post(f"/api/v1/accounts/{account.id}/amulets/{amulet.id}/equip")

    monkeypatch.setattr(ownership_repo, "clear_other_equipped", lambda *a, **k: None)

    response = client.post(f"/api/v1/accounts/{account.id}/amulets/{second_amulet.id}/equip")
    _assert_conflict_not_server_error(response)


def test_equip_rune_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    rune: Rune,
    second_rune: Rune,
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": second_rune.id})
    client.post(f"/api/v1/accounts/{account.id}/runes/{rune.id}/equip", json={"socket_index": 0})

    monkeypatch.setattr(ownership_repo, "clear_rune_socket", lambda *a, **k: None)

    response = client.post(
        f"/api/v1/accounts/{account.id}/runes/{second_rune.id}/equip", json={"socket_index": 0}
    )
    _assert_conflict_not_server_error(response)


def test_equip_skill_race_is_409_not_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    account: UserAccount,
    skill: Skill,
    second_skill: Skill,
) -> None:
    client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    client.post(
        f"/api/v1/accounts/{account.id}/skills",
        json={"skill_id": second_skill.id, "is_unlocked": True},
    )
    client.post(f"/api/v1/accounts/{account.id}/skills/{skill.id}/equip", json={"equipped_slot": 0})

    monkeypatch.setattr(ownership_repo, "clear_skill_slot", lambda *a, **k: None)

    response = client.post(
        f"/api/v1/accounts/{account.id}/skills/{second_skill.id}/equip",
        json={"equipped_slot": 0},
    )
    _assert_conflict_not_server_error(response)
