"""Shared pytest fixtures for backend tests.

Uses an in-memory SQLite database created fresh per test so tests never
touch the development database file and can run fully in parallel /
in isolation.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import build_engine, get_db

# Importing app.domain.models registers every mapped class on
# Base.metadata; without this, create_all() below would create zero
# tables since SQLAlchemy only knows about classes that have been
# imported somewhere in the process.
from app.domain import models  # noqa: F401
from app.domain.models import (
    Amulet,
    Armor,
    ArmorSlot,
    Chapter,
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
from app.main import app


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    # build_engine (not a bare create_engine) so tests get the exact same
    # connection setup as the running application — in particular the
    # PRAGMA foreign_keys=ON that app.db.session.enable_sqlite_foreign_keys
    # applies. Without it, tests would validate a laxer database than the
    # one actually deployed.
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """A TestClient wired to the same in-memory session as the `db`
    fixture, so a test can seed data directly via `db` and then assert
    on what the API returns for it."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# --- Shared single-instance catalog/account fixtures -----------------------
#
# One instance of each type, for tests that just need "a hero exists" /
# "an account exists" without caring about its exact values. Tests that
# need a *second* instance (conflict / auto-replace scenarios) define
# their own local fixture rather than adding one here for everyone.


@pytest.fixture()
def account(db: Session) -> UserAccount:
    instance = UserAccount(display_name="carl")
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def hero(db: Session) -> Hero:
    instance = Hero(name="Hero", hero_class=HeroClass.WARRIOR, rarity=Rarity.EPIC)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def weapon(db: Session) -> Weapon:
    instance = Weapon(name="Weapon", weapon_type="bow", rarity=Rarity.RARE, base_damage=10.0)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def armor_item(db: Session) -> Armor:
    instance = Armor(name="Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.COMMON)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def ring(db: Session) -> Ring:
    instance = Ring(name="Ring", rarity=Rarity.RARE, primary_stat=StatType.ATTACK)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def amulet(db: Session) -> Amulet:
    instance = Amulet(name="Amulet", rarity=Rarity.RARE, primary_stat=StatType.DEFENSE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def pet(db: Session) -> Pet:
    instance = Pet(name="Pet", rarity=Rarity.RARE, bonus_stat=StatType.HEALTH)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def rune(db: Session) -> Rune:
    instance = Rune(name="Rune", rune_type=RuneType.OFFENSE, rarity=Rarity.RARE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def skill(db: Session) -> Skill:
    instance = Skill(name="Skill", skill_type=SkillType.OFFENSIVE)
    db.add(instance)
    db.commit()
    return instance


@pytest.fixture()
def chapter(db: Session) -> Chapter:
    instance = Chapter(number=1, name="Whispering Forest")
    db.add(instance)
    db.commit()
    return instance
