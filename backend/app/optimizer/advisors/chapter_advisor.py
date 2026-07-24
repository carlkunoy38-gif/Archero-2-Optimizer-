"""Chapter Advisor: recommends the best chapter to farm repeatedly, or
the best chapter to push into next, and — when the account is
under-powered for the chapter it should be progressing to — the best
upgrade to close that gap first.

Two objective-driven modes over the same catalog of chapters, not two
separate scoring engines: `objective.name == "farm"` uses
`chapter_scoring.farm_suitability` (comfortable, energy-efficient,
repeatable); every other objective uses `progression_suitability`
(the furthest chapter still safely reachable). This is the same
`ObjectiveProfile` every other advisor takes — "farm" already means
"weigh resource efficiency and clearing multiple things over raw
single-target power" everywhere else in the engine, so reusing it here
for "which chapter" instead of "which skill/gear/upgrade" is the same
concept, not a new one.

When the top *progression* pick is currently unsafe
(`chapter_scoring.clear_safety` is 0 — the account is under-powered for
it), `advise_for_account` cross-calls `upgrade_advisor.advise_for_account`
and folds its top recommendation into that chapter's `summary`/`reasons`
— reusing the Upgrade Advisor rather than re-deriving "what should I
upgrade" logic here, which is exactly the "if a new advisor needs
functionality another advisor already has, reuse it" rule the rest of
`app/optimizer/` follows.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.models import Chapter
from app.optimizer import chapter_scoring, objectives
from app.optimizer.advisors import upgrade_advisor
from app.optimizer.context import BuildContext, build_context
from app.optimizer.objectives import ObjectiveProfile
from app.optimizer.results import AdvisorResult, ScoredOption
from app.services import account_service, catalog_service

#: Large enough to cover any realistic chapter catalog in one page —
#: this advisor needs *every* chapter, not a paginated slice the way
#: `GET /chapters` serves one to a client.
_ALL_CHAPTERS_LIMIT = 10_000


def score_chapter(
    context: BuildContext, chapter: Chapter, objective: ObjectiveProfile = objectives.BALANCED
) -> ScoredOption[Chapter]:
    """Score one chapter for farming or progression suitability
    (depending on `objective`). Pure function — no I/O — so it's
    directly unit-testable without a database."""

    gap = chapter_scoring.power_gap_for_chapter(context, chapter)
    safety = chapter_scoring.clear_safety(gap)
    is_farm_mode = objective.name == "farm"

    if is_farm_mode:
        score = chapter_scoring.farm_suitability(context, chapter, objective)
    else:
        score = chapter_scoring.progression_suitability(context, chapter, objective)

    label = f"Chapter {chapter.number} ({chapter.name})"
    reasons = (
        f"{label}: recommended combat power {chapter.recommended_combat_power:.0f}, "
        f"your combat power {context.combat_power:.0f} (ratio {gap:.2f})",
        f"Clear safety factor: {safety:.2f} (0 = too risky, 1 = fully safe)",
        f"Energy cost per attempt: {chapter.energy_cost}",
    )

    if safety <= 0.0:
        summary = f"{label} is too far above your current power to attempt safely right now."
    elif is_farm_mode:
        summary = f"{label} is a safe, energy-efficient chapter to farm repeatedly."
    else:
        summary = f"{label} is the furthest chapter you can safely push into next."

    return ScoredOption(option=chapter, score=score, summary=summary, reasons=reasons)


def advise(
    context: BuildContext,
    candidates: Sequence[Chapter],
    objective: ObjectiveProfile = objectives.BALANCED,
) -> AdvisorResult[Chapter]:
    """Rank every candidate chapter, best first. Ties break on catalog
    id ascending, same as every other advisor."""

    if not candidates:
        raise ValueError("advise() requires at least one candidate chapter")

    scored = [score_chapter(context, chapter, objective) for chapter in candidates]
    scored.sort(key=lambda scored_option: (-scored_option.score, scored_option.option.id))
    return AdvisorResult(ranked=tuple(scored))


def _with_upgrade_suggestion(
    top: ScoredOption[Chapter], upgrade_top: ScoredOption[upgrade_advisor.UpgradeOption]
) -> ScoredOption[Chapter]:
    augmented_reasons = (*top.reasons, f"Upgrade first: {upgrade_top.summary}")
    augmented_summary = (
        f"{top.summary} You're currently under-powered for it — consider this first: "
        f"{upgrade_top.summary}"
    )
    return ScoredOption(
        option=top.option, score=top.score, summary=augmented_summary, reasons=augmented_reasons
    )


def advise_for_account(
    db: Session, account_id: int, objective_name: str = "balanced"
) -> AdvisorResult[Chapter]:
    """DB-aware entry point: loads the account's build and every
    catalog chapter (raising `NotFoundError` for a missing account, an
    unknown objective name, or an empty chapter catalog), delegates to
    the pure `advise` above, then — in progression mode, when the top
    pick isn't currently safe — folds in the Upgrade Advisor's top
    recommendation rather than leaving the player with no next step."""

    account = account_service.get_account_detail(db, account_id)
    context = build_context(account)
    objective = objectives.resolve(objective_name)

    chapters = catalog_service.list_chapters(db, limit=_ALL_CHAPTERS_LIMIT, offset=0)
    if not chapters:
        raise NotFoundError("No chapters in the catalog yet")

    result = advise(context, chapters, objective)

    if objective.name != "farm":
        top = result.recommended
        gap = chapter_scoring.power_gap_for_chapter(context, top.option)
        if chapter_scoring.clear_safety(gap) <= 0.0:
            try:
                upgrade_result = upgrade_advisor.advise_for_account(db, account_id, objective_name)
            except NotFoundError:
                pass
            else:
                augmented_top = _with_upgrade_suggestion(top, upgrade_result.recommended)
                result = AdvisorResult(ranked=(augmented_top, *result.ranked[1:]))

    return result
