"""Tests for POST /api/v1/accounts, GET /api/v1/accounts/{id}, and
PATCH /api/v1/accounts/{id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Chapter, Hero, UserAccount, UserHeroOwnership


def test_create_account_success(client: TestClient) -> None:
    response = client.post("/api/v1/accounts", json={"display_name": "carl"})
    assert response.status_code == 201
    body = response.json()
    assert body["display_name"] == "carl"
    assert body["gold"] == 0
    assert body["gems"] == 0
    assert body["energy"] == 0
    assert body["combat_power"] == 0.0
    assert body["current_chapter_id"] is None
    assert "id" in body
    assert "created_at" in body


def test_create_account_with_resources_and_chapter(client: TestClient, chapter: Chapter) -> None:
    response = client.post(
        "/api/v1/accounts",
        json={
            "display_name": "carl",
            "gold": 100,
            "gems": 5,
            "energy": 30,
            "combat_power": 1234.5,
            "current_chapter_id": chapter.id,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["gold"] == 100
    assert body["current_chapter_id"] == chapter.id


def test_create_account_duplicate_display_name_is_conflict(client: TestClient) -> None:
    client.post("/api/v1/accounts", json={"display_name": "carl"})
    response = client.post("/api/v1/accounts", json={"display_name": "carl"})
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["type"] == "conflict"
    assert "carl" in body["error"]["message"]


def test_create_account_duplicate_name_rollback_leaves_session_usable(
    client: TestClient,
) -> None:
    """The failed insert's rollback must not corrupt the session — a
    later, unrelated request in the same process should still work."""

    client.post("/api/v1/accounts", json={"display_name": "carl"})
    conflict = client.post("/api/v1/accounts", json={"display_name": "carl"})
    assert conflict.status_code == 409

    recovered = client.post("/api/v1/accounts", json={"display_name": "someone-else"})
    assert recovered.status_code == 201


def test_create_account_nonexistent_chapter_is_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/accounts", json={"display_name": "carl", "current_chapter_id": 999}
    )
    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_create_account_rejects_negative_gold(client: TestClient) -> None:
    response = client.post("/api/v1/accounts", json={"display_name": "carl", "gold": -1})
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "validation_error"


def test_create_account_rejects_blank_display_name(client: TestClient) -> None:
    response = client.post("/api/v1/accounts", json={"display_name": ""})
    assert response.status_code == 422


def test_get_account_detail_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/accounts/999999")
    assert response.status_code == 404


def test_get_account_detail_includes_owned_items_and_progress(
    client: TestClient, db: Session, account: UserAccount, hero: Hero, chapter: Chapter
) -> None:
    db.add(UserHeroOwnership(account_id=account.id, hero_id=hero.id, level=5, stars=2))
    db.commit()

    response = client.put(
        f"/api/v1/accounts/{account.id}/chapters/{chapter.id}/progress",
        json={"stars_earned": 3, "cleared": True, "attempts": 4},
    )
    assert response.status_code == 200

    response = client.get(f"/api/v1/accounts/{account.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == account.id
    assert len(body["heroes"]) == 1
    assert body["heroes"][0]["hero_id"] == hero.id
    assert body["heroes"][0]["level"] == 5
    assert len(body["chapter_progress"]) == 1
    assert body["chapter_progress"][0]["stars_earned"] == 3
    assert body["chapter_progress"][0]["cleared"] is True


def test_update_account_resources(client: TestClient, account: UserAccount) -> None:
    response = client.patch(f"/api/v1/accounts/{account.id}", json={"gold": 500})
    assert response.status_code == 200
    body = response.json()
    assert body["gold"] == 500
    # Untouched fields stay at their previous value.
    assert body["gems"] == 0


def test_update_account_current_chapter(
    client: TestClient, account: UserAccount, chapter: Chapter
) -> None:
    response = client.patch(
        f"/api/v1/accounts/{account.id}", json={"current_chapter_id": chapter.id}
    )
    assert response.status_code == 200
    assert response.json()["current_chapter_id"] == chapter.id


def test_update_account_current_chapter_to_null_clears_it(
    client: TestClient, db: Session, account: UserAccount, chapter: Chapter
) -> None:
    account.current_chapter_id = chapter.id
    db.commit()

    response = client.patch(
        f"/api/v1/accounts/{account.id}", json={"current_chapter_id": None}
    )
    assert response.status_code == 200
    assert response.json()["current_chapter_id"] is None


def test_update_account_nonexistent_chapter_is_not_found(
    client: TestClient, account: UserAccount
) -> None:
    response = client.patch(
        f"/api/v1/accounts/{account.id}", json={"current_chapter_id": 999999}
    )
    assert response.status_code == 404


def test_update_account_not_found(client: TestClient) -> None:
    response = client.patch("/api/v1/accounts/999999", json={"gold": 10})
    assert response.status_code == 404


def test_update_account_rejects_negative_energy(client: TestClient, account: UserAccount) -> None:
    response = client.patch(f"/api/v1/accounts/{account.id}", json={"energy": -1})
    assert response.status_code == 422
