import { useState } from 'react'
import { Button, Select, TextInput } from './ui'

export interface CatalogOption {
  id: number
  label: string
}

export interface OwnershipEntry {
  ownershipId: number
  catalogId: number
  level: number
  starLevel: number | null
  equipped: boolean
  extraLabel?: string
}

interface OwnershipSectionProps {
  title: string
  equippedLabel: string
  hasStarLevel: boolean
  catalog: CatalogOption[]
  entries: OwnershipEntry[]
  onAdd: (catalogId: number, level: number, starLevel: number) => Promise<void>
  onUpdateLevel: (catalogId: number, level: number, starLevel: number) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}

/** One account-owned catalog type (hero/weapon/armor/ring/amulet/pet):
 * a list of owned rows plus an "add another" control. The seven
 * ownership types share this exact shape closely enough that giving
 * each its own copy of this component would just be duplication —
 * rune and skill selection are genuinely different (extra equip
 * parameters, no simple level/star fields) and get their own
 * components instead of being forced in here. */
export function OwnershipSection({
  title,
  equippedLabel,
  hasStarLevel,
  catalog,
  entries,
  onAdd,
  onUpdateLevel,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: OwnershipSectionProps) {
  const ownedCatalogIds = new Set(entries.map((e) => e.catalogId))
  const available = catalog.filter((item) => !ownedCatalogIds.has(item.id))
  const [addCatalogId, setAddCatalogId] = useState<string>('')
  const [addLevel, setAddLevel] = useState('1')
  const [addStarLevel, setAddStarLevel] = useState('0')
  const [addBusy, setAddBusy] = useState(false)

  async function handleAdd() {
    if (!addCatalogId) return
    setAddBusy(true)
    try {
      await onAdd(Number(addCatalogId), Number(addLevel) || 1, Number(addStarLevel) || 0)
      setAddCatalogId('')
      setAddLevel('1')
      setAddStarLevel('0')
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err))
    } finally {
      setAddBusy(false)
    }
  }

  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h4>
      <div className="space-y-2">
        {entries.length === 0 && <p className="text-sm text-slate-500">None owned yet.</p>}
        {entries.map((entry) => (
          <OwnershipRow
            key={entry.ownershipId}
            entry={entry}
            label={catalog.find((c) => c.id === entry.catalogId)?.label ?? `#${entry.catalogId}`}
            equippedLabel={equippedLabel}
            hasStarLevel={hasStarLevel}
            onUpdateLevel={onUpdateLevel}
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
            <option value="">Add {title.toLowerCase()}...</option>
            {available.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </Select>
          <label className="text-xs text-slate-400">
            Lvl{' '}
            <TextInput
              type="number"
              min={1}
              value={addLevel}
              onChange={(e) => setAddLevel(e.target.value)}
              className="w-16"
            />
          </label>
          {hasStarLevel && (
            <label className="text-xs text-slate-400">
              Stars{' '}
              <TextInput
                type="number"
                min={0}
                value={addStarLevel}
                onChange={(e) => setAddStarLevel(e.target.value)}
                className="w-16"
              />
            </label>
          )}
          <Button onClick={handleAdd} disabled={!addCatalogId || addBusy}>
            {addBusy ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

function OwnershipRow({
  entry,
  label,
  equippedLabel,
  hasStarLevel,
  onUpdateLevel,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: {
  entry: OwnershipEntry
  label: string
  equippedLabel: string
  hasStarLevel: boolean
  onUpdateLevel: (catalogId: number, level: number, starLevel: number) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}) {
  const [level, setLevel] = useState(String(entry.level))
  const [starLevel, setStarLevel] = useState(String(entry.starLevel ?? 0))
  const [busy, setBusy] = useState(false)
  const dirty = level !== String(entry.level) || starLevel !== String(entry.starLevel ?? 0)
  const [actionOn, actionOff] = equippedLabel === 'Active' ? ['Activate', 'Deactivate'] : ['Equip', 'Unequip']

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
      {entry.extraLabel && <span className="text-slate-400">{entry.extraLabel}</span>}
      <label className="text-xs text-slate-400">
        Lvl{' '}
        <TextInput
          type="number"
          min={1}
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="w-16"
        />
      </label>
      {hasStarLevel && (
        <label className="text-xs text-slate-400">
          Stars{' '}
          <TextInput
            type="number"
            min={0}
            value={starLevel}
            onChange={(e) => setStarLevel(e.target.value)}
            className="w-16"
          />
        </label>
      )}
      {dirty && (
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() =>
            run(() => onUpdateLevel(entry.catalogId, Number(level) || 1, Number(starLevel) || 0))
          }
        >
          Save
        </Button>
      )}
      {entry.equipped ? (
        <Button variant="secondary" disabled={busy} onClick={() => run(() => onUnequip(entry.catalogId))}>
          {actionOff}
        </Button>
      ) : (
        <Button disabled={busy} onClick={() => run(() => onEquip(entry.catalogId))}>
          {actionOn}
        </Button>
      )}
      <Button variant="danger" disabled={busy} onClick={() => run(() => onRemove(entry.catalogId))}>
        Remove
      </Button>
      {entry.equipped && <span className="text-xs font-medium text-emerald-400">{equippedLabel}</span>}
    </div>
  )
}
