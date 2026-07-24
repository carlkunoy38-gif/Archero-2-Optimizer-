"""Projects a hypothetical change onto a `BuildContext`, without ever
mutating the original — the mechanism every advisor uses to answer "how
much does *this specific* change move the needle on this specific
build," instead of scoring a candidate generically by its category.

`replace_contribution` is the one generic primitive: given what a build
currently gets from something (a skill, an equipped item, an item at
its current level) and what it would get instead, it returns a new
context with the difference applied. Every advisor's "simulate a
candidate" step is one call to it:

- Skill Advisor (`apply_skill`): before is nothing (a skill isn't
  replacing another skill), after is the candidate skill's
  `SkillEffect` total (`context.skill_effect_contribution`).
- Gear Advisor: before is the currently equipped item's contribution
  (or nothing, if the slot is empty), after is a candidate owned
  item's contribution at its own level/star
  (`context.weapon_contribution` / `armor_contribution` / ...).
- Upgrade Advisor: before is an owned item's contribution at its
  *current* level, after is the same item at a hypothetical higher
  level — the only difference from Gear Advisor is which two
  contributions are being compared, not the mechanism.

Pure function, no I/O — callers pass in whatever catalog rows they
already loaded (e.g. `Skill.effects` must already be eager-loaded, see
`app.repositories.skill_repository.get_skill`).
"""

from __future__ import annotations

import dataclasses

from app.domain.models import Skill
from app.optimizer.context import BuildContext, skill_effect_contribution


def replace_contribution(
    context: BuildContext, before: dict[str, float], after: dict[str, float]
) -> BuildContext:
    """Return a new `BuildContext` with `before`'s contribution removed
    and `after`'s added — i.e. `after - before` applied to each field
    either dict touches. Passing an empty `before` is a pure addition
    (nothing currently there); an empty `after` is a pure removal.
    Fields absent from both dicts are left untouched."""

    fields = set(before) | set(after)
    updates: dict[str, float] = {}
    for context_field in fields:
        delta = after.get(context_field, 0.0) - before.get(context_field, 0.0)
        if delta != 0.0:
            updates[context_field] = getattr(context, context_field) + delta

    if not updates:
        return context
    # Contribution dicts only ever key onto BuildContext's float fields
    # (never hero_level/selected_skill_ids), but mypy can't see that
    # through a dynamically-keyed dict.
    return dataclasses.replace(context, **updates)  # type: ignore[arg-type]


def apply_skill(context: BuildContext, skill: Skill) -> BuildContext:
    """Return a new `BuildContext` as if `skill` were additionally
    selected — a pure addition of its `SkillEffect` total, via
    `replace_contribution` with nothing being replaced."""

    return replace_contribution(context, before={}, after=skill_effect_contribution(skill))
