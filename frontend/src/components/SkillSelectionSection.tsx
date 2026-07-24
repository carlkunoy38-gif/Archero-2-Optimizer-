import { useState } from 'react'
import { Button, Select, TextInput } from './ui'
import type { CatalogOption } from './OwnershipSection'

export interface SkillSelectionEntry {
  ownershipId: number
  catalogId: number
  isUnlocked: boolean
  equippedSlot: number | null
}

interface SkillSelectionSectionProps {
  catalog: CatalogOption[]
  entries: SkillSelectionEntry[]
  onAdd: (catalogId: number, isUnlocked: boolean) => Promise<void>
  onSetUnlocked: (catalogId: number, isUnlocked: boolean) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number, equippedSlot: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}

/** Skill selections have no level/star fields, and equipping needs an
 * `equippedSlot`, plus an `isUnlocked` gate a skill must pass before it
 * can be equipped at all — different enough from the gear ownership
 * types to warrant its own component rather than forcing it into
 * `OwnershipSection`. These are the same skills the Build Optimizer
 * page picks candidates from. */
export function SkillSelectionSection({
  catalog,
  entries,
  onAdd,
  onSetUnlocked,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: SkillSelectionSectionProps) {
  const owned = new Set(entries.map((e) => e.catalogId))
  const available = catalog.filter((item) => !owned.has(item.id))
  const [addCatalogId, setAddCatalogId] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleAdd() {
    if (!addCatalogId) return
    setBusy(true)
    try {
      await onAdd(Number(addCatalogId), true)
      setAddCatalogId('')
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Skills unlocked
      </h4>
      <div className="space-y-2">
        {entries.length === 0 && <p className="text-sm text-slate-500">None unlocked yet.</p>}
        {entries.map((entry) => (
          <SkillRow
            key={entry.ownershipId}
            entry={entry}
            label={catalog.find((c) => c.id === entry.catalogId)?.label ?? `#${entry.catalogId}`}
            onSetUnlocked={onSetUnlocked}
            onRemove={onRemove}
            onEquip={onEquip}
            onUnequip={onUnequip}
            onError={onError}
          />
        ))}
      </div>
      {available.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-800 pt-3">
          <Select value={addCatalogId} onChange={(e) => setAddCatalogId(e.target.value)}>
            <option value="">Unlock skill...</option>
            {available.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </Select>
          <Button onClick={handleAdd} disabled={!addCatalogId || busy}>
            {busy ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

function SkillRow({
  entry,
  label,
  onSetUnlocked,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: {
  entry: SkillSelectionEntry
  label: string
  onSetUnlocked: (catalogId: number, isUnlocked: boolean) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number, equippedSlot: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}) {
  const [slot, setSlot] = useState('0')
  const [busy, setBusy] = useState(false)

  async function run(action: () => Promise<void>) {
    setBusy(true)
    try {
      await action()
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md bg-slate-950/60 px-3 py-2 text-sm">
      <span className="min-w-32 font-medium text-slate-100">{label}</span>
      <label className="flex items-center gap-1 text-xs text-slate-400">
        <input
          type="checkbox"
          checked={entry.isUnlocked}
          disabled={busy}
          onChange={(e) => run(() => onSetUnlocked(entry.catalogId, e.target.checked))}
        />
        Unlocked
      </label>
      {entry.isUnlocked &&
        (entry.equippedSlot !== null ? (
          <>
            <span className="text-xs text-slate-400">Slot {entry.equippedSlot}</span>
            <Button variant="secondary" disabled={busy} onClick={() => run(() => onUnequip(entry.catalogId))}>
              Unequip
            </Button>
          </>
        ) : (
          <>
            <label className="text-xs text-slate-400">
              Slot{' '}
              <TextInput
                type="number"
                min={0}
                value={slot}
                onChange={(e) => setSlot(e.target.value)}
                className="w-16"
              />
            </label>
            <Button disabled={busy} onClick={() => run(() => onEquip(entry.catalogId, Number(slot) || 0))}>
              Equip
            </Button>
          </>
        ))}
      <Button variant="danger" disabled={busy} onClick={() => run(() => onRemove(entry.catalogId))}>
        Remove
      </Button>
      {entry.equippedSlot !== null && (
        <span className="text-xs font-medium text-emerald-400">Equipped</span>
      )}
    </div>
  )
}
