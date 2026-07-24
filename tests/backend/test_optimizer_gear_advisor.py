"""Tests for `app.optimizer.advisors.gear_advisor`.

The property that matters most: candidates always come from the
account's *owned* items (never a client-submitted id list), and the
currently-equipped item is scored the same way every other candidate
is — as "what would my build look like with this equipped" — so
"switching would make things worse" shows up as a lower score for the
alternative, not as some special-cased baseline.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import (
    Amulet,
    Armor,
    ArmorSlot,
    Rarity,
    Ring,
    StatType,
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserRingOwnership,
    UserWeaponOwnership,
    Weapon,
)
from app.optimizer import objectives
from app.optimizer.advisors import gear_advisor
from app.optimizer.advisors.gear_advisor import GearCategory, GearOption
from app.optimizer.context import BuildContext


def _context(**overrides: float | int | None) -> BuildContext:
    defaults: dict[str, float | int | None] = {
        "account_id": 1,
        "hero_level": 1,
        "attack": 0.0,
        "defense": 0.0,
        "max_hp": 0.0,
        "attack_speed": 0.0,
        "crit_chance": 0.0,
        "crit_damage": 0.0,
        "movement_speed": 0.0,
        "life_steal": 0.0,
        "dodge": 0.0,
        "resource_gain": 0.0,
        "combat_power": 0.0,
        "recommended_combat_power": None,
    }
    defaults.update(overrides)
    return BuildContext(**defaults)  # type: ignore[arg-type]


def _option(catalog_id: int, name: str, equipped: bool) -> GearOption:
    return GearOption(
        category=GearCategory.WEAPON,
        ownership_id=catalog_id,
        catalog_id=catalog_id,
        name=name,
        is_currently_equipped=equipped,
    )


# --- Pure score_item/advise -------------------------------------------


def test_currently_equipped_item_scores_the_unmodified_baseline() -> None:
    context = _context(attack=200.0)
    option = _option(1, "Dragon Bow", equipped=True)

    scored = gear_advisor.score_item(
        context,
        option,
        current_contribution={"attack": 80.0},
        candidate_contribution={"attack": 80.0},
    )

    assert scored.score == objectives.BALANCED.evaluate(context)
    assert "no measurable effect" in scored.summary.lower()


def test_switching_to_a_worse_item_scores_lower_than_keeping_current() -> None:
    context = _context(attack=200.0)
    current = _option(1, "Dragon Bow", equipped=True)
    worse = _option(2, "Rusty Dagger", equipped=False)

    current_scored = gear_advisor.score_item(
        context,
        current,
        current_contribution={"attack": 100.0},
        candidate_contribution={"attack": 100.0},
    )
    worse_scored = gear_advisor.score_item(
        context,
        worse,
        current_contribution={"attack": 100.0},
        candidate_contribution={"attack": 20.0},
    )

    assert current_scored.score > worse_scored.score


def test_advise_ranks_the_highest_contribution_item_first() -> None:
    context = _context(attack=200.0)
    weak = (_option(1, "Weak", equipped=True), {"attack": 50.0})
    strong = (_option(2, "Strong", equipped=False), {"attack": 150.0})

    result = gear_advisor.advise(context, [weak, strong], current_contribution={"attack": 50.0})

    assert result.recommended.option.name == "Strong"


def test_advise_requires_at_least_one_candidate() -> None:
    with pytest.raises(ValueError):
        gear_advisor.advise(_context(), [], current_contribution={})


def test_advise_breaks_ties_deterministically_by_catalog_id() -> None:
    context = _context(attack=100.0)
    twin_a = (_option(5, "Twin A", equipped=False), {"attack": 10.0})
    twin_b = (_option(2, "Twin B", equipped=False), {"attack": 10.0})

    forward = gear_advisor.advise(context, [twin_a, twin_b], current_contribution={})
    backward = gear_advisor.advise(context, [twin_b, twin_a], current_contribution={})

    assert forward.recommended.option.catalog_id == backward.recommended.option.catalog_id == 2


# --- DB-aware advise_for_account ---------------------------------------


def test_advise_for_account_ranks_owned_weapons(db: Session, account: UserAccount) -> None:
    strong = Weapon(
        name="Strong Bow", weapon_type="bow", rarity=Rarity.LEGENDARY, base_damage=100.0
    )
    weak = Weapon(name="Weak Dagger", weapon_type="dagger", rarity=Rarity.COMMON, base_damage=10.0)
    db.add_all([strong, weak])
    db.commit()
    db.add(
        UserWeaponOwnership(
            account_id=account.id, weapon_id=strong.id, level=1, is_equipped=False
        )
    )
    db.add(
        UserWeaponOwnership(account_id=account.id, weapon_id=weak.id, level=1, is_equipped=True)
    )
    db.commit()

    result = gear_advisor.advise_for_account(db, account.id, GearCategory.WEAPON)

    assert result.recommended.option.catalog_id == strong.id


def test_advise_for_account_armor_requires_slot(db: Session, account: UserAccount) -> None:
    with pytest.raises(NotFoundError):
        gear_advisor.advise_for_account(db, account.id, GearCategory.ARMOR, armor_slot=None)


def test_advise_for_account_armor_scopes_by_slot(db: Session, account: UserAccount) -> None:
    helmet = Armor(
        name="Good Helmet", slot=ArmorSlot.HELMET, rarity=Rarity.EPIC, base_defense=50.0
    )
    boots = Armor(
        name="Great Boots", slot=ArmorSlot.BOOTS, rarity=Rarity.LEGENDARY, base_defense=200.0
    )
    db.add_all([helmet, boots])
    db.commit()
    db.add(
        UserArmorOwnership(
            account_id=account.id, armor_id=helmet.id, armor=helmet, level=1, is_equipped=True
        )
    )
    db.add(
        UserArmorOwnership(
            account_id=account.id, armor_id=boots.id, armor=boots, level=1, is_equipped=True
        )
    )
    db.commit()

    result = gear_advisor.advise_for_account(
        db, account.id, GearCategory.ARMOR, armor_slot=ArmorSlot.HELMET
    )

    assert len(result.ranked) == 1
    assert result.recommended.option.catalog_id == helmet.id


def test_advise_for_account_raises_not_found_for_missing_account(db: Session) -> None:
    with pytest.raises(NotFoundError):
        gear_advisor.advise_for_account(db, 999999, GearCategory.WEAPON)


def test_advise_for_account_raises_not_found_for_unknown_objective(
    db: Session, account: UserAccount, weapon: Weapon
) -> None:
    db.add(
        UserWeaponOwnership(account_id=account.id, weapon_id=weapon.id, level=1, is_equipped=True)
    )
    db.commit()

    with pytest.raises(NotFoundError):
        gear_advisor.advise_for_account(
            db, account.id, GearCategory.WEAPON, objective_name="nonsense"
        )


def test_advise_for_account_raises_not_found_when_nothing_owned(
    db: Session, account: UserAccount
) -> None:
    with pytest.raises(NotFoundError):
        gear_advisor.advise_for_account(db, account.id, GearCategory.RING)


def test_advise_for_account_objective_changes_the_recommendation(
    db: Session, account: UserAccount
) -> None:
    # A ring boosting resource_gain should win under "farm" (which
    # weighs utility heavily) but lose to a ring boosting attack under
    # "boss" (which weighs offense heavily).
    # FARM weighs utility (0.005 offense / 3.0 utility) heavily enough
    # that even a much bigger attack number loses to a small resource
    # gain; BOSS weighs offense enough (0.04 offense / 0.5 utility)
    # that a large attack number outweighs a small resource gain — see
    # weights.OBJECTIVE_WEIGHTS.
    farm_ring = Ring(
        name="Farmer's Ring",
        rarity=Rarity.EPIC,
        primary_stat=StatType.RESOURCE_GAIN,
        primary_stat_value=10.0,
    )
    boss_ring = Ring(
        name="Warrior's Ring",
        rarity=Rarity.EPIC,
        primary_stat=StatType.ATTACK,
        primary_stat_value=200.0,
    )
    db.add_all([farm_ring, boss_ring])
    db.commit()
    db.add(
        UserRingOwnership(account_id=account.id, ring_id=farm_ring.id, level=1, is_equipped=True)
    )
    db.add(
        UserRingOwnership(account_id=account.id, ring_id=boss_ring.id, level=1, is_equipped=False)
    )
    db.commit()

    farm_result = gear_advisor.advise_for_account(
        db, account.id, GearCategory.RING, objective_name="farm"
    )
    boss_result = gear_advisor.advise_for_account(
        db, account.id, GearCategory.RING, objective_name="boss"
    )

    assert farm_result.recommended.option.catalog_id == farm_ring.id
    assert boss_result.recommended.option.catalog_id == boss_ring.id


def test_advise_for_account_amulet_category_works_too(db: Session, account: UserAccount) -> None:
    amulet = Amulet(
        name="Test Amulet",
        rarity=Rarity.RARE,
        primary_stat=StatType.DEFENSE,
        primary_stat_value=20.0,
    )
    db.add(amulet)
    db.commit()
    db.add(
        UserAmuletOwnership(account_id=account.id, amulet_id=amulet.id, level=1, is_equipped=True)
    )
    db.commit()

    result = gear_advisor.advise_for_account(db, account.id, GearCategory.AMULET)

    assert result.recommended.option.catalog_id == amulet.id
