"""Tests for `app.seeds.runes`.

The property that matters most: summing each seeded rune's numeric
effects by type reproduces the account-level totals shown in the
screenshots this data was sourced from exactly — that cross-check is
what makes this "real data" rather than an invented example, and a
future edit to `_RUNES` that breaks the reconciliation should fail loudly
here rather than silently drift from the source.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import EffectType, Rune
from app.seeds.runes import seed_runes


def test_seed_runes_inserts_all_ten_runes(db: Session) -> None:
    inserted = seed_runes(db)

    assert inserted == 10
    assert len(db.scalars(select(Rune)).all()) == 10


def test_seed_runes_is_idempotent(db: Session) -> None:
    seed_runes(db)

    second_run_inserted = seed_runes(db)

    assert second_run_inserted == 0
    assert len(db.scalars(select(Rune)).all()) == 10


def test_seed_runes_reconciles_with_source_account_totals(db: Session) -> None:
    # Real numbers read off the account "Details" screenshot this data
    # was sourced from — see app/seeds/runes.py's module docstring.
    expected_totals = {
        EffectType.CIRCLE_DAMAGE_BONUS: 30.0,
        EffectType.SPRITE_DAMAGE_BONUS: 15.0,
        EffectType.PLANT_DAMAGE_BONUS: 15.0,
        EffectType.ICE_DAMAGE_BONUS: 10.0,
        EffectType.POISON_DAMAGE_BONUS: 20.0,
        EffectType.LIGHTNING_DAMAGE_BONUS: 10.0,
        EffectType.FIRE_DAMAGE_BONUS: 20.0,
    }

    seed_runes(db)

    runes = db.scalars(select(Rune)).all()
    totals: dict[EffectType, float] = {}
    for rune in runes:
        for effect in rune.effects:
            totals[effect.effect_type] = totals.get(effect.effect_type, 0.0) + effect.value

    for effect_type, expected_value in expected_totals.items():
        assert totals[effect_type] == expected_value
