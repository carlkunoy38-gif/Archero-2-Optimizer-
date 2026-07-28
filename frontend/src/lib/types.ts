// Mirrors the backend's Pydantic schemas (backend/app/schemas/*.py) and
// domain enums (backend/app/domain/models/enums.py). Kept as plain
// interfaces/unions, not generated, since the backend has no OpenAPI
// codegen step wired up yet — if the two drift, the dev-mode API calls
// will surface it immediately (wrong field name -> undefined at
// runtime), which is an acceptable tradeoff for a project this size.

// --- Enums ------------------------------------------------------------

export type Rarity = 'common' | 'rare' | 'epic' | 'legendary' | 'mythic' | 'chaotic'
export type HeroClass = 'warrior' | 'mage' | 'ranger' | 'assassin' | 'support'
export type ArmorSlot = 'helmet' | 'chest' | 'gloves' | 'boots'
export type StatType =
  | 'attack'
  | 'health'
  | 'defense'
  | 'crit_chance'
  | 'crit_damage'
  | 'attack_speed'
  | 'movement_speed'
  | 'life_steal'
  | 'dodge'
  | 'resource_gain'
export type RuneType = 'offense' | 'defense' | 'utility'
export type SkillType = 'offensive' | 'defensive' | 'utility' | 'movement'
export type EffectType =
  | 'projectile_count'
  | 'bounce_count'
  | 'attack_speed_multiplier'
  | 'crit_chance_bonus'
  | 'crit_damage_bonus'
  | 'defense_bonus'
  | 'max_hp_bonus'
  | 'dodge_bonus'
  | 'movement_speed_bonus'
  | 'resource_gain_bonus'
  | 'life_steal_bonus'
  | 'attack_bonus'
  | 'circle_damage_bonus'
  | 'sprite_damage_bonus'
  | 'plant_damage_bonus'
  | 'ice_damage_bonus'
  | 'poison_damage_bonus'
  | 'lightning_damage_bonus'
  | 'fire_damage_bonus'

// --- Catalog (read-only) -----------------------------------------------

export interface HeroRead {
  id: number
  name: string
  hero_class: HeroClass
  rarity: Rarity
  base_hp: number
  base_attack: number
  base_defense: number
  base_attack_speed: number
  signature_skill_description: string | null
  description: string | null
}

export interface WeaponRead {
  id: number
  name: string
  weapon_type: string
  rarity: Rarity
  base_damage: number
  base_attack_speed: number
  crit_chance_bonus: number
  special_effect: string | null
  description: string | null
}

export interface ArmorRead {
  id: number
  name: string
  slot: ArmorSlot
  rarity: Rarity
  base_defense: number
  base_hp: number
  special_effect: string | null
  description: string | null
}

export interface RingRead {
  id: number
  name: string
  rarity: Rarity
  primary_stat: StatType
  primary_stat_value: number
  special_effect: string | null
  description: string | null
}

export interface AmuletRead {
  id: number
  name: string
  rarity: Rarity
  primary_stat: StatType
  primary_stat_value: number
  special_effect: string | null
  description: string | null
}

export interface PetRead {
  id: number
  name: string
  rarity: Rarity
  bonus_stat: StatType
  bonus_stat_value: number
  ability_description: string | null
  description: string | null
}

export interface RuneEffectRead {
  effect_type: EffectType
  value: number
}

export interface RuneRead {
  id: number
  name: string
  rune_type: RuneType
  rarity: Rarity
  effect_description: string | null
  effects: RuneEffectRead[]
}

export interface SkillEffectRead {
  effect_type: EffectType
  value: number
}

export interface SkillRead {
  id: number
  name: string
  skill_type: SkillType
  tier: number
  description: string | null
  effects: SkillEffectRead[]
}

export interface ChapterRead {
  id: number
  number: number
  name: string
  boss_name: string | null
  recommended_combat_power: number
  energy_cost: number
  rewards_summary: string | null
  description: string | null
}

// --- Account ------------------------------------------------------------

export interface AccountRead {
  id: number
  display_name: string
  gold: number
  gems: number
  energy: number
  combat_power: number
  current_chapter_id: number | null
}

export interface AccountCreate {
  display_name: string
  gold?: number
  gems?: number
  energy?: number
  combat_power?: number
  current_chapter_id?: number | null
}

export interface AccountUpdate {
  gold?: number
  gems?: number
  energy?: number
  combat_power?: number
  current_chapter_id?: number | null
}

// --- Ownership ------------------------------------------------------------

export interface HeroOwnershipRead {
  id: number
  hero_id: number
  level: number
  stars: number
  is_active: boolean
}

export interface WeaponOwnershipRead {
  id: number
  weapon_id: number
  level: number
  star_level: number
  is_equipped: boolean
}

export interface ArmorOwnershipRead {
  id: number
  armor_id: number
  slot: ArmorSlot
  level: number
  star_level: number
  is_equipped: boolean
}

export interface RingOwnershipRead {
  id: number
  ring_id: number
  level: number
  is_equipped: boolean
}

export interface AmuletOwnershipRead {
  id: number
  amulet_id: number
  level: number
  is_equipped: boolean
}

export interface PetOwnershipRead {
  id: number
  pet_id: number
  level: number
  is_active: boolean
}

export interface RuneOwnershipRead {
  id: number
  rune_id: number
  level: number
  is_equipped: boolean
  socket_index: number | null
}

export interface SkillSelectionRead {
  id: number
  skill_id: number
  is_unlocked: boolean
  equipped_slot: number | null
}

export interface ChapterProgressRead {
  id: number
  chapter_id: number
  stars_earned: number
  cleared: boolean
  attempts: number
}

export interface AccountDetailRead extends AccountRead {
  heroes: HeroOwnershipRead[]
  weapons: WeaponOwnershipRead[]
  armor_pieces: ArmorOwnershipRead[]
  rings: RingOwnershipRead[]
  amulets: AmuletOwnershipRead[]
  pets: PetOwnershipRead[]
  runes: RuneOwnershipRead[]
  skill_selections: SkillSelectionRead[]
  chapter_progress: ChapterProgressRead[]
}

// --- Optimizer ------------------------------------------------------------

export type ObjectiveName = 'balanced' | 'boss' | 'farm' | 'survival'

export interface SkillAdviceRequest {
  account_id: number
  candidate_skill_ids: number[]
  objective?: ObjectiveName
}

export interface SkillScoreBreakdown {
  skill_id: number
  name: string
  skill_type: SkillType
  score: number
  summary: string
  reasons: string[]
}

export interface SkillAdviceResponse {
  recommended_skill_id: number
  ranking: SkillScoreBreakdown[]
}

export type GearCategory = 'weapon' | 'armor' | 'ring' | 'amulet' | 'pet'

export interface GearAdviceRequest {
  account_id: number
  category: GearCategory
  armor_slot?: ArmorSlot | null
  objective?: ObjectiveName
}

export interface GearScoreBreakdown {
  category: GearCategory
  catalog_id: number
  name: string
  is_currently_equipped: boolean
  score: number
  summary: string
  reasons: string[]
}

export interface GearAdviceResponse {
  recommended_catalog_id: number
  ranking: GearScoreBreakdown[]
}

export type UpgradeCategory = 'hero' | 'weapon' | 'armor' | 'ring' | 'amulet' | 'pet' | 'rune'

export interface UpgradeAdviceRequest {
  account_id: number
  objective?: ObjectiveName
}

export interface UpgradeScoreBreakdown {
  category: UpgradeCategory
  // The account's actual ownership row id — catalog_id alone isn't
  // unique across categories (a Hero and a Weapon can share catalog
  // id 1), since one response spans every ownable category at once.
  ownership_id: number
  catalog_id: number
  name: string
  from_level: number
  to_level: number
  gold_cost: number
  score: number
  summary: string
  reasons: string[]
}

export interface UpgradeRecommendedOption {
  category: UpgradeCategory
  ownership_id: number
  catalog_id: number
}

export interface UpgradeAdviceResponse {
  recommended: UpgradeRecommendedOption
  ranking: UpgradeScoreBreakdown[]
}

export interface ChapterAdviceRequest {
  account_id: number
  objective?: ObjectiveName
}

export interface ChapterScoreBreakdown {
  chapter_id: number
  number: number
  name: string
  score: number
  summary: string
  reasons: string[]
}

export interface ChapterAdviceResponse {
  recommended_chapter_id: number
  ranking: ChapterScoreBreakdown[]
}

// --- Error envelope ---------------------------------------------------

export interface ErrorEnvelope {
  error: {
    type: string
    message: string
    details?: unknown
  }
}
