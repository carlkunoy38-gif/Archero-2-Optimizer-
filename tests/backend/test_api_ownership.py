"""Tests for the account ownership sub-resources: POST/PATCH/DELETE for
each of the seven ownership types, plus skill selection and chapter
progress.

Not every type gets the full matrix repeated — hero ownership below is
exercised most thoroughly (create/duplicate/invalid-fk/negative/update/
delete/404s) since the CRUD shape is identical across all seven; the
others focus on what's distinctive about them (armor's derived slot,
rune/skill's slot fields being absent from the create/update schema).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.domain.models import (
    Amulet,
    Armor,
    Chapter,
    Hero,
    Pet,
    Ring,
    Rune,
    Skill,
    UserAccount,
    Weapon,
)

# --- Hero: full CRUD matrix ------------------------------------------------


def test_create_hero_ownership(client: TestClient, account: UserAccount, hero: Hero) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id, "level": 3, "stars": 1}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["hero_id"] == hero.id
    assert body["level"] == 3
    assert body["stars"] == 1
    assert body["is_active"] is False


def test_create_hero_ownership_duplicate_is_conflict(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    response = client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    assert response.status_code == 409
    assert response.json()["error"]["type"] == "conflict"


def test_create_hero_ownership_invalid_hero_id_is_not_found(
    client: TestClient, account: UserAccount
) -> None:
    response = client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": 999999})
    assert response.status_code == 404


def test_create_hero_ownership_invalid_account_id_is_not_found(
    client: TestClient, hero: Hero
) -> None:
    response = client.post("/api/v1/accounts/999999/heroes", json={"hero_id": hero.id})
    assert response.status_code == 404


def test_create_hero_ownership_rejects_negative_stars(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id, "stars": -1}
    )
    assert response.status_code == 422


def test_create_hero_ownership_rejects_level_below_one(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id, "level": 0}
    )
    assert response.status_code == 422


def test_update_hero_ownership(client: TestClient, account: UserAccount, hero: Hero) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    response = client.patch(
        f"/api/v1/accounts/{account.id}/heroes/{hero.id}", json={"level": 10, "stars": 4}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["level"] == 10
    assert body["stars"] == 4


def test_update_hero_ownership_not_found(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    response = client.patch(f"/api/v1/accounts/{account.id}/heroes/{hero.id}", json={"level": 2})
    assert response.status_code == 404


def test_update_hero_ownership_cannot_set_is_active(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    # is_active isn't a field on HeroOwnershipUpdate at all — extra
    # fields are simply ignored by Pydantic, not a validation error.
    response = client.patch(
        f"/api/v1/accounts/{account.id}/heroes/{hero.id}", json={"is_active": True}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_delete_hero_ownership(client: TestClient, account: UserAccount, hero: Hero) -> None:
    client.post(f"/api/v1/accounts/{account.id}/heroes", json={"hero_id": hero.id})
    response = client.delete(f"/api/v1/accounts/{account.id}/heroes/{hero.id}")
    assert response.status_code == 204

    # It's gone: a second delete is a 404.
    response = client.delete(f"/api/v1/accounts/{account.id}/heroes/{hero.id}")
    assert response.status_code == 404


def test_delete_hero_ownership_not_found(
    client: TestClient, account: UserAccount, hero: Hero
) -> None:
    response = client.delete(f"/api/v1/accounts/{account.id}/heroes/{hero.id}")
    assert response.status_code == 404


# --- Weapon -----------------------------------------------------------------


def test_weapon_ownership_crud(client: TestClient, account: UserAccount, weapon: Weapon) -> None:
    create = client.post(
        f"/api/v1/accounts/{account.id}/weapons", json={"weapon_id": weapon.id}
    )
    assert create.status_code == 201
    assert create.json()["is_equipped"] is False

    update = client.patch(
        f"/api/v1/accounts/{account.id}/weapons/{weapon.id}", json={"star_level": 2}
    )
    assert update.status_code == 200
    assert update.json()["star_level"] == 2

    delete = client.delete(f"/api/v1/accounts/{account.id}/weapons/{weapon.id}")
    assert delete.status_code == 204


# --- Armor: slot is derived, never client-writable --------------------------


def test_create_armor_ownership_derives_slot_from_catalog(
    client: TestClient, account: UserAccount, armor_item: Armor
) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id}
    )
    assert response.status_code == 201
    assert response.json()["slot"] == armor_item.slot.value


def test_create_armor_ownership_ignores_client_supplied_slot(
    client: TestClient, account: UserAccount, armor_item: Armor
) -> None:
    """`slot` isn't a field on `ArmorOwnershipCreate` — sending one is
    simply ignored, not honored, confirming a client can't override the
    catalog-derived value even by trying."""

    response = client.post(
        f"/api/v1/accounts/{account.id}/armor",
        json={"armor_id": armor_item.id, "slot": "boots"},
    )
    assert response.status_code == 201
    assert response.json()["slot"] == armor_item.slot.value
    assert response.json()["slot"] != "boots"


def test_armor_ownership_update_and_delete(
    client: TestClient, account: UserAccount, armor_item: Armor
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/armor", json={"armor_id": armor_item.id})

    update = client.patch(
        f"/api/v1/accounts/{account.id}/armor/{armor_item.id}", json={"level": 5}
    )
    assert update.status_code == 200
    assert update.json()["level"] == 5

    delete = client.delete(f"/api/v1/accounts/{account.id}/armor/{armor_item.id}")
    assert delete.status_code == 204


# --- Ring / Amulet / Pet ----------------------------------------------------


def test_ring_ownership_crud(client: TestClient, account: UserAccount, ring: Ring) -> None:
    create = client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": ring.id})
    assert create.status_code == 201

    duplicate = client.post(f"/api/v1/accounts/{account.id}/rings", json={"ring_id": ring.id})
    assert duplicate.status_code == 409

    delete = client.delete(f"/api/v1/accounts/{account.id}/rings/{ring.id}")
    assert delete.status_code == 204


def test_amulet_ownership_crud(client: TestClient, account: UserAccount, amulet: Amulet) -> None:
    create = client.post(
        f"/api/v1/accounts/{account.id}/amulets", json={"amulet_id": amulet.id}
    )
    assert create.status_code == 201

    update = client.patch(
        f"/api/v1/accounts/{account.id}/amulets/{amulet.id}", json={"level": 3}
    )
    assert update.status_code == 200
    assert update.json()["level"] == 3


def test_pet_ownership_crud(client: TestClient, account: UserAccount, pet: Pet) -> None:
    create = client.post(f"/api/v1/accounts/{account.id}/pets", json={"pet_id": pet.id})
    assert create.status_code == 201
    assert create.json()["is_active"] is False

    delete = client.delete(f"/api/v1/accounts/{account.id}/pets/{pet.id}")
    assert delete.status_code == 204


# --- Rune: socket_index is not client-settable via create/update -----------


def test_create_rune_ownership_has_no_socket_by_default(
    client: TestClient, account: UserAccount, rune: Rune
) -> None:
    response = client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    assert response.status_code == 201
    assert response.json()["socket_index"] is None
    assert response.json()["is_equipped"] is False


def test_update_rune_ownership_ignores_socket_index_field(
    client: TestClient, account: UserAccount, rune: Rune
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/runes", json={"rune_id": rune.id})
    response = client.patch(
        f"/api/v1/accounts/{account.id}/runes/{rune.id}",
        json={"level": 2, "socket_index": 0},
    )
    assert response.status_code == 200
    assert response.json()["level"] == 2
    assert response.json()["socket_index"] is None


# --- Skill selection --------------------------------------------------------


def test_create_skill_selection(client: TestClient, account: UserAccount, skill: Skill) -> None:
    response = client.post(
        f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id, "is_unlocked": True}
    )
    assert response.status_code == 201
    assert response.json()["is_unlocked"] is True
    assert response.json()["equipped_slot"] is None


def test_update_skill_selection_unlocks_it(
    client: TestClient, account: UserAccount, skill: Skill
) -> None:
    client.post(f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id})
    response = client.patch(
        f"/api/v1/accounts/{account.id}/skills/{skill.id}", json={"is_unlocked": True}
    )
    assert response.status_code == 200
    assert response.json()["is_unlocked"] is True


def test_delete_skill_selection(client: TestClient, account: UserAccount, skill: Skill) -> None:
    client.post(f"/api/v1/accounts/{account.id}/skills", json={"skill_id": skill.id})
    response = client.delete(f"/api/v1/accounts/{account.id}/skills/{skill.id}")
    assert response.status_code == 204


# --- Chapter progress (upsert) ----------------------------------------------


def test_upsert_chapter_progress_creates_when_missing(
    client: TestClient, account: UserAccount, chapter: Chapter
) -> None:
    response = client.put(
        f"/api/v1/accounts/{account.id}/chapters/{chapter.id}/progress",
        json={"stars_earned": 2, "attempts": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["stars_earned"] == 2
    assert body["attempts"] == 1
    assert body["cleared"] is False


def test_upsert_chapter_progress_updates_existing(
    client: TestClient, account: UserAccount, chapter: Chapter
) -> None:
    client.put(
        f"/api/v1/accounts/{account.id}/chapters/{chapter.id}/progress",
        json={"stars_earned": 1},
    )
    response = client.put(
        f"/api/v1/accounts/{account.id}/chapters/{chapter.id}/progress",
        json={"stars_earned": 3, "cleared": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["stars_earned"] == 3
    assert body["cleared"] is True


def test_upsert_chapter_progress_rejects_negative_attempts(
    client: TestClient, account: UserAccount, chapter: Chapter
) -> None:
    response = client.put(
        f"/api/v1/accounts/{account.id}/chapters/{chapter.id}/progress",
        json={"attempts": -1},
    )
    assert response.status_code == 422


def test_upsert_chapter_progress_nonexistent_chapter_is_not_found(
    client: TestClient, account: UserAccount
) -> None:
    response = client.put(
        f"/api/v1/accounts/{account.id}/chapters/999999/progress", json={"stars_earned": 1}
    )
    assert response.status_code == 404
