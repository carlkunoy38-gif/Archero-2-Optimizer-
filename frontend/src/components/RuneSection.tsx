import { useState } from 'react'
import { Button, Select, TextInput } from './ui'
import type { CatalogOption } from './OwnershipSection'

export interface RuneEntry {
  ownershipId: number
  catalogId: number
  level: number
  equipped: boolean
  socketIndex: number | null
}

interface RuneSectionProps {
  catalog: CatalogOption[]
  entries: RuneEntry[]
  onAdd: (catalogId: number, level: number) => Promise<void>
  onUpdateLevel: (catalogId: number, level: number) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number, socketIndex: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}

/** Runes need a `socketIndex` at equip time (the backend keys "which
 * socket" by a plain int, not a fixed named slot), which is why this
 * isn't just another `OwnershipSection` instance. */
export function RuneSection({
  catalog,
  entries,
  onAdd,
  onUpdateLevel,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: RuneSectionProps) {
  const owned = new Set(entries.map((e) => e.catalogId))
  const available = catalog.filter((item) => !owned.has(item.id))
  const [addCatalogId, setAddCatalogId] = useState('')
  const [addLevel, setAddLevel] = useState('1')
  const [busy, setBusy] = useState(false)

  async function handleAdd() {
    if (!addCatalogId) return
    setBusy(true)
    try {
      await onAdd(Number(addCatalogId), Number(addLevel) || 1)
      setAddCatalogId('')
      setAddLevel('1')
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Runes</h4>
      <div className="space-y-2">
        {entries.length === 0 && <p className="text-sm text-slate-500">None owned yet.</p>}
        {entries.map((entry) => (
          <RuneRow
            key={entry.ownershipId}
            entry={entry}
            label={catalog.find((c) => c.id === entry.catalogId)?.label ?? `#${entry.catalogId}`}
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
            <option value="">Add rune...</option>
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
          <Button onClick={handleAdd} disabled={!addCatalogId || busy}>
            {busy ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

function RuneRow({
  entry,
  label,
  onUpdateLevel,
  onRemove,
  onEquip,
  onUnequip,
  onError,
}: {
  entry: RuneEntry
  label: string
  onUpdateLevel: (catalogId: number, level: number) => Promise<void>
  onRemove: (catalogId: number) => Promise<void>
  onEquip: (catalogId: number, socketIndex: number) => Promise<void>
  onUnequip: (catalogId: number) => Promise<void>
  onError: (message: string) => void
}) {
  const [level, setLevel] = useState(String(entry.level))
  const [socketIndex, setSocketIndex] = useState('0')
  const [busy, setBusy] = useState(false)
  const dirty = level !== String(entry.level)

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
      {dirty && (
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => run(() => onUpdateLevel(entry.catalogId, Number(level) || 1))}
        >
          Save
        </Button>
      )}
      {entry.equipped ? (
        <>
          <span className="text-xs text-slate-400">Socket {entry.socketIndex}</span>
          <Button variant="secondary" disabled={busy} onClick={() => run(() => onUnequip(entry.catalogId))}>
            Unequip
          </Button>
        </>
      ) : (
        <>
          <label className="text-xs text-slate-400">
            Socket{' '}
            <TextInput
              type="number"
              min={0}
              value={socketIndex}
              onChange={(e) => setSocketIndex(e.target.value)}
              className="w-16"
            />
          </label>
          <Button
            disabled={busy}
            onClick={() => run(() => onEquip(entry.catalogId, Number(socketIndex) || 0))}
          >
            Equip
          </Button>
        </>
      )}
      <Button variant="danger" disabled={busy} onClick={() => run(() => onRemove(entry.catalogId))}>
        Remove
      </Button>
      {entry.equipped && <span className="text-xs font-medium text-emerald-400">Equipped</span>}
    </div>
  )
}
