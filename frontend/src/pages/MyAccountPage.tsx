import { useEffect, useState } from 'react'
import { api, ApiError } from '../lib/apiClient'
import type {
  AccountDetailRead,
  AmuletRead,
  ArmorRead,
  ChapterRead,
  HeroRead,
  PetRead,
  RingRead,
  RuneRead,
  SkillRead,
  WeaponRead,
} from '../lib/types'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import { Button, ErrorText, Panel, TextInput } from '../components/ui'
import { OwnershipSection } from '../components/OwnershipSection'
import { RuneSection } from '../components/RuneSection'
import { SkillSelectionSection } from '../components/SkillSelectionSection'
import { ChapterProgressSection } from '../components/ChapterProgressSection'

interface Catalog {
  heroes: HeroRead[]
  weapons: WeaponRead[]
  armor: ArmorRead[]
  rings: RingRead[]
  amulets: AmuletRead[]
  pets: PetRead[]
  runes: RuneRead[]
  skills: SkillRead[]
  chapters: ChapterRead[]
}

export function MyAccountPage() {
  const { accountId, setAccountId } = useCurrentAccount()
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [account, setAccount] = useState<AccountDetailRead | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.listHeroes(),
      api.listWeapons(),
      api.listArmor(),
      api.listRings(),
      api.listAmulets(),
      api.listPets(),
      api.listRunes(),
      api.listSkills(),
      api.listChapters(),
    ])
      .then(([heroes, weapons, armor, rings, amulets, pets, runes, skills, chapters]) => {
        if (!cancelled) {
          setCatalog({ heroes, weapons, armor, rings, amulets, pets, runes, skills, chapters })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err))
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function refresh(id: number) {
    setLoading(true)
    try {
      const detail = await api.getAccount(id)
      setAccount(detail)
      setError(null)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setAccountId(null)
        setAccount(null)
      } else {
        setError(err instanceof Error ? err.message : String(err))
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (accountId === null) {
      setAccount(null)
      setLoading(false)
      return
    }
    void refresh(accountId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId])

  if (!catalog || loading) {
    return <p className="text-slate-400">Loading...</p>
  }

  if (accountId === null || account === null) {
    return (
      <div className="space-y-4">
        {error && <ErrorText>{error}</ErrorText>}
        <AccountPicker
          onCreated={(id) => setAccountId(id)}
          onSwitched={(id) => setAccountId(id)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && <ErrorText>{error}</ErrorText>}

      <Panel>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">{account.display_name}</h2>
            <p className="text-sm text-slate-500">Account #{account.id}</p>
          </div>
          <Button variant="secondary" onClick={() => setAccountId(null)}>
            Switch account
          </Button>
        </div>
      </Panel>

      <Panel title="Core stats">
        <CoreStatsForm
          account={account}
          chapters={catalog.chapters}
          onSave={async (payload) => {
            try {
              await api.updateAccount(account.id, payload)
              await refresh(account.id)
            } catch (err) {
              setError(err instanceof Error ? err.message : String(err))
            }
          }}
        />
      </Panel>

      <Panel title="Hero">
        <OwnershipSection
          title="Heroes"
          equippedLabel="Active"
          hasStarLevel={false}
          catalog={catalog.heroes.map((h) => ({ id: h.id, label: h.name }))}
          entries={account.heroes.map((h) => ({
            ownershipId: h.id,
            catalogId: h.hero_id,
            level: h.level,
            starLevel: h.stars,
            equipped: h.is_active,
          }))}
          onAdd={async (id, level, stars) => {
            await api.addHero(account.id, id, level, stars)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level, stars) => {
            await api.updateHero(account.id, id, level, stars)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeHero(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.activateHero(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.deactivateHero(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Weapon">
        <OwnershipSection
          title="Weapons"
          equippedLabel="Equipped"
          hasStarLevel={true}
          catalog={catalog.weapons.map((w) => ({ id: w.id, label: w.name }))}
          entries={account.weapons.map((w) => ({
            ownershipId: w.id,
            catalogId: w.weapon_id,
            level: w.level,
            starLevel: w.star_level,
            equipped: w.is_equipped,
          }))}
          onAdd={async (id, level, star) => {
            await api.addWeapon(account.id, id, level, star)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level, star) => {
            await api.updateWeapon(account.id, id, level, star)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeWeapon(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.equipWeapon(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipWeapon(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Armor">
        <OwnershipSection
          title="Armor"
          equippedLabel="Equipped"
          hasStarLevel={true}
          catalog={catalog.armor.map((a) => ({ id: a.id, label: `${a.name} (${a.slot})` }))}
          entries={account.armor_pieces.map((a) => ({
            ownershipId: a.id,
            catalogId: a.armor_id,
            level: a.level,
            starLevel: a.star_level,
            equipped: a.is_equipped,
            extraLabel: a.slot,
          }))}
          onAdd={async (id, level, star) => {
            await api.addArmor(account.id, id, level, star)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level, star) => {
            await api.updateArmor(account.id, id, level, star)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeArmor(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.equipArmor(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipArmor(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Ring">
        <OwnershipSection
          title="Rings"
          equippedLabel="Equipped"
          hasStarLevel={false}
          catalog={catalog.rings.map((r) => ({ id: r.id, label: r.name }))}
          entries={account.rings.map((r) => ({
            ownershipId: r.id,
            catalogId: r.ring_id,
            level: r.level,
            starLevel: null,
            equipped: r.is_equipped,
          }))}
          onAdd={async (id, level) => {
            await api.addRing(account.id, id, level)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level) => {
            await api.updateRing(account.id, id, level)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeRing(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.equipRing(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipRing(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Amulet">
        <OwnershipSection
          title="Amulets"
          equippedLabel="Equipped"
          hasStarLevel={false}
          catalog={catalog.amulets.map((a) => ({ id: a.id, label: a.name }))}
          entries={account.amulets.map((a) => ({
            ownershipId: a.id,
            catalogId: a.amulet_id,
            level: a.level,
            starLevel: null,
            equipped: a.is_equipped,
          }))}
          onAdd={async (id, level) => {
            await api.addAmulet(account.id, id, level)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level) => {
            await api.updateAmulet(account.id, id, level)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeAmulet(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.equipAmulet(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipAmulet(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Pet">
        <OwnershipSection
          title="Pets"
          equippedLabel="Active"
          hasStarLevel={false}
          catalog={catalog.pets.map((p) => ({ id: p.id, label: p.name }))}
          entries={account.pets.map((p) => ({
            ownershipId: p.id,
            catalogId: p.pet_id,
            level: p.level,
            starLevel: null,
            equipped: p.is_active,
          }))}
          onAdd={async (id, level) => {
            await api.addPet(account.id, id, level)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level) => {
            await api.updatePet(account.id, id, level)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removePet(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id) => {
            await api.activatePet(account.id, id)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.deactivatePet(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Runes">
        <RuneSection
          catalog={catalog.runes.map((r) => ({ id: r.id, label: `${r.name} (${r.rune_type})` }))}
          entries={account.runes.map((r) => ({
            ownershipId: r.id,
            catalogId: r.rune_id,
            level: r.level,
            equipped: r.is_equipped,
            socketIndex: r.socket_index,
          }))}
          onAdd={async (id, level) => {
            await api.addRune(account.id, id, level)
            await refresh(account.id)
          }}
          onUpdateLevel={async (id, level) => {
            await api.updateRune(account.id, id, level)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeRune(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id, socketIndex) => {
            await api.equipRune(account.id, id, socketIndex)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipRune(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Skills">
        <SkillSelectionSection
          catalog={catalog.skills.map((s) => ({ id: s.id, label: `${s.name} (${s.skill_type})` }))}
          entries={account.skill_selections.map((s) => ({
            ownershipId: s.id,
            catalogId: s.skill_id,
            isUnlocked: s.is_unlocked,
            equippedSlot: s.equipped_slot,
          }))}
          onAdd={async (id, unlocked) => {
            await api.addSkillSelection(account.id, id, unlocked)
            await refresh(account.id)
          }}
          onSetUnlocked={async (id, unlocked) => {
            await api.updateSkillSelection(account.id, id, unlocked)
            await refresh(account.id)
          }}
          onRemove={async (id) => {
            await api.removeSkillSelection(account.id, id)
            await refresh(account.id)
          }}
          onEquip={async (id, slot) => {
            await api.equipSkill(account.id, id, slot)
            await refresh(account.id)
          }}
          onUnequip={async (id) => {
            await api.unequipSkill(account.id, id)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>

      <Panel title="Chapters">
        <ChapterProgressSection
          chapters={catalog.chapters.map((c) => ({ id: c.id, label: `${c.number}. ${c.name}` }))}
          entries={account.chapter_progress.map((p) => ({
            chapterId: p.chapter_id,
            starsEarned: p.stars_earned,
            cleared: p.cleared,
            attempts: p.attempts,
          }))}
          onUpsert={async (id, payload) => {
            await api.upsertChapterProgress(account.id, id, payload)
            await refresh(account.id)
          }}
          onError={setError}
        />
      </Panel>
    </div>
  )
}

function AccountPicker({
  onCreated,
  onSwitched,
}: {
  onCreated: (id: number) => void
  onSwitched: (id: number) => void
}) {
  const [displayName, setDisplayName] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const [switchId, setSwitchId] = useState('')
  const [switching, setSwitching] = useState(false)
  const [switchError, setSwitchError] = useState<string | null>(null)

  async function handleCreate() {
    if (!displayName.trim()) return
    setCreating(true)
    setCreateError(null)
    try {
      const created = await api.createAccount({ display_name: displayName.trim() })
      onCreated(created.id)
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : String(err))
    } finally {
      setCreating(false)
    }
  }

  async function handleSwitch() {
    const id = Number(switchId)
    if (!Number.isInteger(id)) return
    setSwitching(true)
    setSwitchError(null)
    try {
      await api.getAccount(id) // verify it exists before adopting it
      onSwitched(id)
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : String(err))
    } finally {
      setSwitching(false)
    }
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Panel title="Create a new account">
        <div className="flex flex-col gap-2">
          <TextInput
            placeholder="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
          <Button disabled={!displayName.trim() || creating} onClick={handleCreate}>
            {creating ? 'Creating...' : 'Create account'}
          </Button>
          {createError && <ErrorText>{createError}</ErrorText>}
        </div>
      </Panel>
      <Panel title="Switch to an existing account">
        <div className="flex flex-col gap-2">
          <TextInput
            type="number"
            placeholder="Account ID"
            value={switchId}
            onChange={(e) => setSwitchId(e.target.value)}
          />
          <Button disabled={!switchId || switching} onClick={handleSwitch}>
            {switching ? 'Checking...' : 'Switch'}
          </Button>
          {switchError && <ErrorText>{switchError}</ErrorText>}
        </div>
      </Panel>
    </div>
  )
}

function CoreStatsForm({
  account,
  chapters,
  onSave,
}: {
  account: AccountDetailRead
  chapters: ChapterRead[]
  onSave: (payload: {
    gold: number
    gems: number
    energy: number
    combat_power: number
    current_chapter_id: number | null
  }) => Promise<void>
}) {
  const [gold, setGold] = useState(String(account.gold))
  const [gems, setGems] = useState(String(account.gems))
  const [energy, setEnergy] = useState(String(account.energy))
  const [combatPower, setCombatPower] = useState(String(account.combat_power))
  const [chapterId, setChapterId] = useState(String(account.current_chapter_id ?? ''))
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    setSaving(true)
    try {
      await onSave({
        gold: Number(gold) || 0,
        gems: Number(gems) || 0,
        energy: Number(energy) || 0,
        combat_power: Number(combatPower) || 0,
        current_chapter_id: chapterId === '' ? null : Number(chapterId),
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Gold
        <TextInput type="number" min={0} value={gold} onChange={(e) => setGold(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Gems
        <TextInput type="number" min={0} value={gems} onChange={(e) => setGems(e.target.value)} />
      </label>
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Energy
        <TextInput
          type="number"
          min={0}
          value={energy}
          onChange={(e) => setEnergy(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Combat power
        <TextInput
          type="number"
          min={0}
          value={combatPower}
          onChange={(e) => setCombatPower(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-1 text-xs text-slate-400">
        Current chapter
        <select
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-sm text-slate-100"
          value={chapterId}
          onChange={(e) => setChapterId(e.target.value)}
        >
          <option value="">None</option>
          {chapters.map((c) => (
            <option key={c.id} value={c.id}>
              {c.number}. {c.name}
            </option>
          ))}
        </select>
      </label>
      <div className="col-span-full">
        <Button disabled={saving} onClick={handleSave}>
          {saving ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </div>
  )
}
