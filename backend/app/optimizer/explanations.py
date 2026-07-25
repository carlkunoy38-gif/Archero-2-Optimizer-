"""The shared "explanation system" every advisor reports a
recommendation through: turning a before/after `BuildContext` pair into
a player-facing `summary` sentence and a detailed `reasons` breakdown.

This exists so the Gear, Upgrade, and Chapter Advisors don't each
reimplement "which fields changed and by how much" — that logic
started out living only in `skill_advisor.py`; it moved here once a
second advisor needed the exact same thing, which is the whole point
of `app/optimizer/weights.py`'s "one file for every tunable number"
philosophy applied to explanation text instead of numbers.
"""

from __future__ import annotations

import dataclasses

from app.optimizer.context import BuildContext

#: Player-facing description of what changed, keyed by `BuildContext`
#: field name. Only fields something can actually move need an entry; a
#: changed field with no entry falls back to its raw name.
FIELD_DESCRIPTION: dict[str, str] = {
    "attack": "raw attack",
    "defense": "defense",
    "max_hp": "max HP",
    "attack_speed": "attack speed",
    "crit_chance": "crit chance",
    "crit_damage": "crit damage",
    "movement_speed": "movement speed",
    "life_steal": "life steal",
    "dodge": "dodge chance",
    "resource_gain": "resource gain",
    "projectile_count": "projectile count",
    "bounce_count": "bounce/ricochet count",
    "circle_damage": "circle (orbiting) damage",
    "sprite_damage": "sprite summon damage",
    "plant_damage": "plant guardian damage",
    "ice_damage": "ice proc damage",
    "poison_damage": "poison proc damage",
    "lightning_damage": "lightning proc damage",
    "fire_damage": "fire proc damage",
}


def changed_fields(before: BuildContext, after: BuildContext) -> dict[str, tuple[float, float]]:
    """Every numeric `BuildContext` field that differs between two
    contexts, as `{field_name: (old_value, new_value)}`."""

    changed: dict[str, tuple[float, float]] = {}
    for context_field in dataclasses.fields(before):
        if context_field.name not in FIELD_DESCRIPTION:
            continue
        old_value = getattr(before, context_field.name)
        new_value = getattr(after, context_field.name)
        if new_value != old_value:
            changed[context_field.name] = (old_value, new_value)
    return changed


def dominant_field(changed: dict[str, tuple[float, float]]) -> str | None:
    """The changed field with the largest absolute delta — the one
    worth naming in a one-sentence summary. `None` if nothing changed."""

    if not changed:
        return None
    return max(changed, key=lambda name: abs(changed[name][1] - changed[name][0]))


def build_reasons(
    base_label: str,
    changed: dict[str, tuple[float, float]],
    objective_name: str,
    gain: float,
) -> tuple[str, ...]:
    """The detailed, numeric factor-by-factor breakdown: `base_label`
    first (whatever the calling advisor's own baseline is — a skill's
    tier value, an item's equip status, ...), then one line per changed
    field, then the overall marginal objective gain. If nothing
    changed, says so plainly rather than listing an empty diff."""

    reasons: list[str] = [base_label]
    if changed:
        for field_name, (old_value, new_value) in changed.items():
            description = FIELD_DESCRIPTION.get(field_name, field_name)
            reasons.append(
                f"{description}: {old_value:.2f} -> {new_value:.2f} "
                f"({new_value - old_value:+.2f})"
            )
        reasons.append(
            f"Marginal '{objective_name}' objective gain from this change: {gain:+.2f}"
        )
    else:
        reasons.append("No measurable stat change — scored on its baseline alone.")
    return tuple(reasons)


def build_summary(
    subject_name: str,
    changed: dict[str, tuple[float, float]],
    objective_name: str,
    gain: float,
) -> str:
    """One player-facing sentence naming the dominant thing that
    changed, distinct from `reasons`' full numeric breakdown."""

    field = dominant_field(changed)
    if field is None:
        return f"{subject_name} has no measurable effect on your build yet."
    description = FIELD_DESCRIPTION.get(field, field)
    return (
        f"{subject_name} mainly affects your {description} — estimated {objective_name} "
        f"objective value for this change: {gain:+.1f}."
    )
