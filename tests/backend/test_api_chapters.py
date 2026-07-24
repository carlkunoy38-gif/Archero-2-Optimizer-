"""Tests for GET /api/v1/chapters and GET /api/v1/chapters/{chapter_id}."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models import Chapter


def test_list_chapters_empty(client: TestClient) -> None:
    response = client.get("/api/v1/chapters")
    assert response.status_code == 200
    assert response.json() == []


def test_list_chapters_returns_seeded_rows_ordered_by_number(
    client: TestClient, db: Session
) -> None:
    db.add_all([Chapter(number=2, name="Second"), Chapter(number=1, name="First")])
    db.commit()

    response = client.get("/api/v1/chapters")
    assert response.status_code == 200
    body = response.json()
    assert [c["number"] for c in body] == [1, 2]


def test_list_chapters_respects_limit_and_offset(client: TestClient, db: Session) -> None:
    db.add_all([Chapter(number=i, name=f"Chapter {i}") for i in range(1, 6)])
    db.commit()

    response = client.get("/api/v1/chapters", params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_chapter_detail(client: TestClient, chapter: Chapter) -> None:
    response = client.get(f"/api/v1/chapters/{chapter.id}")
    assert response.status_code == 200
    assert response.json()["id"] == chapter.id


def test_get_chapter_detail_missing_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/chapters/999999")
    assert response.status_code == 404
