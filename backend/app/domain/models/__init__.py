"""ORM models.

Every model class is re-exported here so that Alembic's ``env.py`` and
application code can do ``from app.domain.models import Hero, Weapon, ...``
and, critically, so that importing this package is enough to register
every mapped class on ``Base.metadata`` before ``create_all`` or an
Alembic autogenerate runs.
"""

from app.domain.models.amulet import Amulet
from app.domain.models.armor import Armor
from app.domain.models.chapter import Chapter
from app.domain.models.enums import (
    ArmorSlot,
    EffectType,
    HeroClass,
    Rarity,
    RuneType,
    SkillType,
    StatType,
)
from app.domain.models.hero import Hero
from app.domain.models.pet import Pet
from app.domain.models.ring import Ring
from app.domain.models.rune import Rune
from app.domain.models.skill import Skill
from app.domain.models.skill_effect import SkillEffect
from app.domain.models.user_account import (
    UserAccount,
    UserAmuletOwnership,
    UserArmorOwnership,
    UserChapterProgress,
    UserHeroOwnership,
    UserPetOwnership,
    UserRingOwnership,
    UserRuneOwnership,
    UserSkillSelection,
    UserWeaponOwnership,
)
from app.domain.models.weapon import Weapon

__all__ = [
    "Amulet",
    "Armor",
    "ArmorSlot",
    "Chapter",
    "EffectType",
    "Hero",
    "HeroClass",
    "Pet",
    "Rarity",
    "Ring",
    "Rune",
    "RuneType",
    "Skill",
    "SkillEffect",
    "SkillType",
    "StatType",
    "UserAccount",
    "UserAmuletOwnership",
    "UserArmorOwnership",
    "UserChapterProgress",
    "UserHeroOwnership",
    "UserPetOwnership",
    "UserRingOwnership",
    "UserRuneOwnership",
    "UserSkillSelection",
    "UserWeaponOwnership",
    "Weapon",
]
