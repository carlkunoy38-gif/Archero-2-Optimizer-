// Thin typed wrapper around the backend REST API
// (backend/app/api/router.py). Every error response the backend can
// return uses one envelope shape — {error: {type, message, details}}
// (see backend/app/api/error_handlers.py) — so this is the one place
// that needs to know how to unwrap it into a throwable ApiError.

import type {
  AccountCreate,
  AccountDetailRead,
  AccountRead,
  AccountUpdate,
  AmuletOwnershipRead,
  AmuletRead,
  ArmorOwnershipRead,
  ArmorRead,
  ChapterAdviceRequest,
  ChapterAdviceResponse,
  ChapterProgressRead,
  ChapterRead,
  ErrorEnvelope,
  GearAdviceRequest,
  GearAdviceResponse,
  HeroOwnershipRead,
  HeroRead,
  PetOwnershipRead,
  PetRead,
  RingOwnershipRead,
  RingRead,
  RuneOwnershipRead,
  RuneRead,
  SkillAdviceRequest,
  SkillAdviceResponse,
  SkillRead,
  SkillSelectionRead,
  UpgradeAdviceRequest,
  UpgradeAdviceResponse,
  WeaponOwnershipRead,
  WeaponRead,
} from './types'

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  readonly type: string
  readonly status: number
  readonly details: unknown

  constructor(message: string, type: string, status: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.type = type
    this.status = status
    this.details = details
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })

  if (!response.ok) {
    const envelope = (await response.json().catch(() => null)) as ErrorEnvelope | null
    throw new ApiError(
      envelope?.error.message ?? response.statusText,
      envelope?.error.type ?? 'unknown_error',
      response.status,
      envelope?.error.details,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

const get = <T>(path: string) => request<T>(path)
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
const patch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
const put = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'PUT', body: JSON.stringify(body) })
const del = (path: string) => request<void>(path, { method: 'DELETE' })

export const api = {
  // --- Catalog (read-only) ---
  listHeroes: () => get<HeroRead[]>('/heroes?limit=200'),
  listWeapons: () => get<WeaponRead[]>('/weapons?limit=200'),
  listArmor: () => get<ArmorRead[]>('/armor?limit=200'),
  listRings: () => get<RingRead[]>('/rings?limit=200'),
  listAmulets: () => get<AmuletRead[]>('/amulets?limit=200'),
  listPets: () => get<PetRead[]>('/pets?limit=200'),
  listRunes: () => get<RuneRead[]>('/runes?limit=200'),
  listSkills: () => get<SkillRead[]>('/skills?limit=200'),
  listChapters: () => get<ChapterRead[]>('/chapters?limit=200'),

  // --- Account ---
  createAccount: (payload: AccountCreate) => post<AccountRead>('/accounts', payload),
  getAccount: (accountId: number) => get<AccountDetailRead>(`/accounts/${accountId}`),
  updateAccount: (accountId: number, payload: AccountUpdate) =>
    patch<AccountRead>(`/accounts/${accountId}`, payload),

  // --- Ownership: create/update/delete ---
  addHero: (accountId: number, heroId: number, level: number, stars: number) =>
    post<HeroOwnershipRead>(`/accounts/${accountId}/heroes`, { hero_id: heroId, level, stars }),
  updateHero: (accountId: number, heroId: number, level: number, stars: number) =>
    patch<HeroOwnershipRead>(`/accounts/${accountId}/heroes/${heroId}`, { level, stars }),
  removeHero: (accountId: number, heroId: number) =>
    del(`/accounts/${accountId}/heroes/${heroId}`),

  addWeapon: (accountId: number, weaponId: number, level: number, starLevel: number) =>
    post<WeaponOwnershipRead>(`/accounts/${accountId}/weapons`, {
      weapon_id: weaponId,
      level,
      star_level: starLevel,
    }),
  updateWeapon: (accountId: number, weaponId: number, level: number, starLevel: number) =>
    patch<WeaponOwnershipRead>(`/accounts/${accountId}/weapons/${weaponId}`, {
      level,
      star_level: starLevel,
    }),
  removeWeapon: (accountId: number, weaponId: number) =>
    del(`/accounts/${accountId}/weapons/${weaponId}`),

  addArmor: (accountId: number, armorId: number, level: number, starLevel: number) =>
    post<ArmorOwnershipRead>(`/accounts/${accountId}/armor`, {
      armor_id: armorId,
      level,
      star_level: starLevel,
    }),
  updateArmor: (accountId: number, armorId: number, level: number, starLevel: number) =>
    patch<ArmorOwnershipRead>(`/accounts/${accountId}/armor/${armorId}`, {
      level,
      star_level: starLevel,
    }),
  removeArmor: (accountId: number, armorId: number) =>
    del(`/accounts/${accountId}/armor/${armorId}`),

  addRing: (accountId: number, ringId: number, level: number) =>
    post<RingOwnershipRead>(`/accounts/${accountId}/rings`, { ring_id: ringId, level }),
  updateRing: (accountId: number, ringId: number, level: number) =>
    patch<RingOwnershipRead>(`/accounts/${accountId}/rings/${ringId}`, { level }),
  removeRing: (accountId: number, ringId: number) =>
    del(`/accounts/${accountId}/rings/${ringId}`),

  addAmulet: (accountId: number, amuletId: number, level: number) =>
    post<AmuletOwnershipRead>(`/accounts/${accountId}/amulets`, { amulet_id: amuletId, level }),
  updateAmulet: (accountId: number, amuletId: number, level: number) =>
    patch<AmuletOwnershipRead>(`/accounts/${accountId}/amulets/${amuletId}`, { level }),
  removeAmulet: (accountId: number, amuletId: number) =>
    del(`/accounts/${accountId}/amulets/${amuletId}`),

  addPet: (accountId: number, petId: number, level: number) =>
    post<PetOwnershipRead>(`/accounts/${accountId}/pets`, { pet_id: petId, level }),
  updatePet: (accountId: number, petId: number, level: number) =>
    patch<PetOwnershipRead>(`/accounts/${accountId}/pets/${petId}`, { level }),
  removePet: (accountId: number, petId: number) => del(`/accounts/${accountId}/pets/${petId}`),

  addRune: (accountId: number, runeId: number, level: number) =>
    post<RuneOwnershipRead>(`/accounts/${accountId}/runes`, { rune_id: runeId, level }),
  updateRune: (accountId: number, runeId: number, level: number) =>
    patch<RuneOwnershipRead>(`/accounts/${accountId}/runes/${runeId}`, { level }),
  removeRune: (accountId: number, runeId: number) => del(`/accounts/${accountId}/runes/${runeId}`),

  addSkillSelection: (accountId: number, skillId: number, isUnlocked: boolean) =>
    post<SkillSelectionRead>(`/accounts/${accountId}/skills`, {
      skill_id: skillId,
      is_unlocked: isUnlocked,
    }),
  updateSkillSelection: (accountId: number, skillId: number, isUnlocked: boolean) =>
    patch<SkillSelectionRead>(`/accounts/${accountId}/skills/${skillId}`, {
      is_unlocked: isUnlocked,
    }),
  removeSkillSelection: (accountId: number, skillId: number) =>
    del(`/accounts/${accountId}/skills/${skillId}`),

  upsertChapterProgress: (
    accountId: number,
    chapterId: number,
    payload: { stars_earned?: number; cleared?: boolean; attempts?: number },
  ) => put<ChapterProgressRead>(`/accounts/${accountId}/chapters/${chapterId}/progress`, payload),

  // --- Equip/activate actions ---
  activateHero: (accountId: number, heroId: number) =>
    post<HeroOwnershipRead>(`/accounts/${accountId}/heroes/${heroId}/activate`),
  deactivateHero: (accountId: number, heroId: number) =>
    post<HeroOwnershipRead>(`/accounts/${accountId}/heroes/${heroId}/deactivate`),
  activatePet: (accountId: number, petId: number) =>
    post<PetOwnershipRead>(`/accounts/${accountId}/pets/${petId}/activate`),
  deactivatePet: (accountId: number, petId: number) =>
    post<PetOwnershipRead>(`/accounts/${accountId}/pets/${petId}/deactivate`),
  equipWeapon: (accountId: number, weaponId: number) =>
    post<WeaponOwnershipRead>(`/accounts/${accountId}/weapons/${weaponId}/equip`),
  unequipWeapon: (accountId: number, weaponId: number) =>
    post<WeaponOwnershipRead>(`/accounts/${accountId}/weapons/${weaponId}/unequip`),
  equipArmor: (accountId: number, armorId: number) =>
    post<ArmorOwnershipRead>(`/accounts/${accountId}/armor/${armorId}/equip`),
  unequipArmor: (accountId: number, armorId: number) =>
    post<ArmorOwnershipRead>(`/accounts/${accountId}/armor/${armorId}/unequip`),
  equipRing: (accountId: number, ringId: number) =>
    post<RingOwnershipRead>(`/accounts/${accountId}/rings/${ringId}/equip`),
  unequipRing: (accountId: number, ringId: number) =>
    post<RingOwnershipRead>(`/accounts/${accountId}/rings/${ringId}/unequip`),
  equipAmulet: (accountId: number, amuletId: number) =>
    post<AmuletOwnershipRead>(`/accounts/${accountId}/amulets/${amuletId}/equip`),
  unequipAmulet: (accountId: number, amuletId: number) =>
    post<AmuletOwnershipRead>(`/accounts/${accountId}/amulets/${amuletId}/unequip`),
  equipRune: (accountId: number, runeId: number, socketIndex: number) =>
    post<RuneOwnershipRead>(`/accounts/${accountId}/runes/${runeId}/equip`, {
      socket_index: socketIndex,
    }),
  unequipRune: (accountId: number, runeId: number) =>
    post<RuneOwnershipRead>(`/accounts/${accountId}/runes/${runeId}/unequip`),
  equipSkill: (accountId: number, skillId: number, equippedSlot: number) =>
    post<SkillSelectionRead>(`/accounts/${accountId}/skills/${skillId}/equip`, {
      equipped_slot: equippedSlot,
    }),
  unequipSkill: (accountId: number, skillId: number) =>
    post<SkillSelectionRead>(`/accounts/${accountId}/skills/${skillId}/unequip`),

  // --- Optimizer ---
  adviseSkills: (payload: SkillAdviceRequest) =>
    post<SkillAdviceResponse>('/optimizer/skills/advise', payload),
  adviseGear: (payload: GearAdviceRequest) =>
    post<GearAdviceResponse>('/optimizer/gear/advise', payload),
  adviseUpgrade: (payload: UpgradeAdviceRequest) =>
    post<UpgradeAdviceResponse>('/optimizer/upgrade/advise', payload),
  adviseChapters: (payload: ChapterAdviceRequest) =>
    post<ChapterAdviceResponse>('/optimizer/chapters/advise', payload),
}
