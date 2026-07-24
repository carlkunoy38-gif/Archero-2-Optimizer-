"""Projects a candidate skill's structured effects onto a `BuildContext`.

This is the mechanism that lets the Skill Advisor score two same-tier,
same-category skills differently: instead of asking "is an OFFENSIVE
skill generically good for this build," it asks "how much does *this
specific* skill's effects move the needle on this specific build,"
by comparing `engine.py`/`objectives.py` scores of the build before and
after `apply_skill`. See `app.optimizer.advisors.skill_advisor.score_skill`
for where that comparison happens.

Pure function, no I/O — `Skill.effects` must already be loaded (see
`app.repositories.skill_repository.get_skill`, which eager-loads it).
"""

from __future__ import annotations

import dataclasses

from app.domain.models import Skill
from app.optimizer.context import _EFFECT_TYPE_FIELD, BuildContext


def apply_skill(context: BuildContext, skill: Skill) -> BuildContext:
    """Return a new `BuildContext` as if `skill` were additionally
    selected, by adding each of its `SkillEffect` values onto the
    matching field. Effect types with no mapped field (none exist today,
    but `EffectType` may grow ahead of `_EFFECT_TYPE_FIELD`) are ignored
    rather than raising, same as `build_context`'s own handling of
    unmapped stat/rune types. The original `context` is never mutated —
    it's a frozen dataclass, and this returns a new instance."""

    updates: dict[str, float] = {}
    for effect in skill.effects:
        effect_field = _EFFECT_TYPE_FIELD.get(effect.effect_type)
        if effect_field is None:
            continue
        current = updates.get(effect_field, getattr(context, effect_field))
        updates[effect_field] = current + effect.value

    if not updates:
        return context
    # _EFFECT_TYPE_FIELD only ever maps onto BuildContext's float fields
    # (never hero_level/selected_skill_ids), but mypy can't see that
    # through a dynamically-keyed dict — see the same pattern's absence
    # in context.py, where the fields are assigned individually instead.
    return dataclasses.replace(context, **updates)  # type: ignore[arg-type]
