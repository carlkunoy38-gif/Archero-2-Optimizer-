"""Generic result shapes every advisor reports a recommendation in.

This is the actual "all advisors reuse the same engine" contract at the
data level — a skill choice today, a gear/upgrade/rune/farming-route
choice for a future advisor, all come back as a ranked list of scored
options with reasons. It is deliberately *just* a data shape, not a
forced common method signature: comparing skill candidates isn't
structurally the same problem as comparing gear candidates (different
input shapes, different DB lookups), so a shared abstract base class
with one real implementation behind it would be premature abstraction.
What's actually shared is `engine.py`'s scoring primitives and this
reporting shape — not a forced `Advisor.recommend()` interface.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoredOption[T]:
    """One candidate's score and the human-readable reasons behind it."""

    option: T
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AdvisorResult[T]:
    """`ranked` is sorted descending by score; `ranked[0]` is the
    recommendation. Never empty — advisors that would otherwise return
    an empty result raise instead (see e.g.
    `app.optimizer.advisors.skill_advisor.advise`)."""

    ranked: tuple[ScoredOption[T], ...]

    @property
    def recommended(self) -> ScoredOption[T]:
        return self.ranked[0]
