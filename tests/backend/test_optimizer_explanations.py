"""Unit tests for `app.optimizer.explanations` — the shared "why"
formatting every advisor (Skill, Gear, Upgrade) builds its `summary`/
`reasons` from.
"""

from __future__ import annotations

from app.optimizer import explanations
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


def test_changed_fields_reports_only_fields_that_actually_differ() -> None:
    before = _context(attack=100.0, defense=50.0)
    after = _context(attack=150.0, defense=50.0)

    changed = explanations.changed_fields(before, after)

    assert changed == {"attack": (100.0, 150.0)}


def test_changed_fields_is_empty_for_identical_contexts() -> None:
    before = _context(attack=100.0)
    after = _context(attack=100.0)

    assert explanations.changed_fields(before, after) == {}


def test_changed_fields_ignores_non_field_context_attributes() -> None:
    # account_id/hero_level/recommended_combat_power/selected_skill_ids
    # aren't in FIELD_DESCRIPTION and must never show up as a "stat
    # change" even if they differ between the two contexts.
    before = _context(account_id=1, hero_level=1)
    after = _context(account_id=2, hero_level=9)

    assert explanations.changed_fields(before, after) == {}


def test_dominant_field_picks_the_largest_absolute_delta() -> None:
    changed = {"attack": (100.0, 110.0), "defense": (50.0, 5.0)}

    assert explanations.dominant_field(changed) == "defense"


def test_dominant_field_is_none_when_nothing_changed() -> None:
    assert explanations.dominant_field({}) is None


def test_build_reasons_includes_base_label_first() -> None:
    reasons = explanations.build_reasons("Tier 3 baseline value: 30.0", {}, "balanced", 0.0)
    assert reasons[0] == "Tier 3 baseline value: 30.0"


def test_build_reasons_lists_every_changed_field_and_the_overall_gain() -> None:
    changed = {"attack": (100.0, 150.0), "defense": (20.0, 20.0 + 5.0)}

    reasons = explanations.build_reasons("base", changed, "balanced", 3.5)

    assert any("raw attack: 100.00 -> 150.00 (+50.00)" in reason for reason in reasons)
    assert any("defense: 20.00 -> 25.00 (+5.00)" in reason for reason in reasons)
    assert reasons[-1] == "Marginal 'balanced' objective gain from this change: +3.50"


def test_build_reasons_is_honest_when_nothing_changed() -> None:
    reasons = explanations.build_reasons("base", {}, "balanced", 0.0)
    assert reasons[-1] == "No measurable stat change — scored on its baseline alone."


def test_build_summary_names_the_dominant_field() -> None:
    changed = {"attack": (100.0, 105.0), "max_hp": (200.0, 400.0)}

    summary = explanations.build_summary("Thing", changed, "farm", 12.3)

    assert "max HP" in summary
    assert "farm" in summary
    assert "+12.3" in summary


def test_build_summary_is_honest_when_nothing_changed() -> None:
    summary = explanations.build_summary("Thing", {}, "balanced", 0.0)
    assert summary == "Thing has no measurable effect on your build yet."
