import { useState } from 'react'
import { Button, Select, TextInput } from './ui'
import type { CatalogOption } from './OwnershipSection'

export interface ChapterProgressEntry {
  chapterId: number
  starsEarned: number
  cleared: boolean
  attempts: number
}

interface ChapterProgressSectionProps {
  chapters: CatalogOption[]
  entries: ChapterProgressEntry[]
  onUpsert: (
    chapterId: number,
    payload: { stars_earned: number; cleared: boolean; attempts: number },
  ) => Promise<void>
  onError: (message: string) => void
}

/** Chapter progress is an upsert keyed by chapter, not a normal
 * "own -> equip" ownership row, so it gets its own section rather than
 * reusing `OwnershipSection`. */
export function ChapterProgressSection({
  chapters,
  entries,
  onUpsert,
  onError,
}: ChapterProgressSectionProps) {
  const tracked = new Set(entries.map((e) => e.chapterId))
  const untracked = chapters.filter((c) => !tracked.has(c.id))
  const [addChapterId, setAddChapterId] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleAdd() {
    if (!addChapterId) return
    setBusy(true)
    try {
      await onUpsert(Number(addChapterId), { stars_earned: 0, cleared: false, attempts: 0 })
      setAddChapterId('')
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Chapter progress
      </h4>
      <div className="space-y-2">
        {entries.length === 0 && <p className="text-sm text-slate-500">No chapters tracked yet.</p>}
        {entries.map((entry) => (
          <ProgressRow
            key={entry.chapterId}
            entry={entry}
            label={chapters.find((c) => c.id === entry.chapterId)?.label ?? `#${entry.chapterId}`}
            onUpsert={onUpsert}
            onError={onError}
          />
        ))}
      </div>
      {untracked.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-800 pt-3">
          <Select value={addChapterId} onChange={(e) => setAddChapterId(e.target.value)}>
            <option value="">Track chapter...</option>
            {untracked.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </Select>
          <Button onClick={handleAdd} disabled={!addChapterId || busy}>
            {busy ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

function ProgressRow({
  entry,
  label,
  onUpsert,
  onError,
}: {
  entry: ChapterProgressEntry
  label: string
  onUpsert: (
    chapterId: number,
    payload: { stars_earned: number; cleared: boolean; attempts: number },
  ) => Promise<void>
  onError: (message: string) => void
}) {
  const [stars, setStars] = useState(String(entry.starsEarned))
  const [attempts, setAttempts] = useState(String(entry.attempts))
  const [cleared, setCleared] = useState(entry.cleared)
  const [busy, setBusy] = useState(false)
  const dirty =
    stars !== String(entry.starsEarned) ||
    attempts !== String(entry.attempts) ||
    cleared !== entry.cleared

  async function handleSave() {
    setBusy(true)
    try {
      await onUpsert(entry.chapterId, {
        stars_earned: Number(stars) || 0,
        cleared,
        attempts: Number(attempts) || 0,
      })
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
        Stars{' '}
        <TextInput
          type="number"
          min={0}
          value={stars}
          onChange={(e) => setStars(e.target.value)}
          className="w-16"
        />
      </label>
      <label className="text-xs text-slate-400">
        Attempts{' '}
        <TextInput
          type="number"
          min={0}
          value={attempts}
          onChange={(e) => setAttempts(e.target.value)}
          className="w-16"
        />
      </label>
      <label className="flex items-center gap-1 text-xs text-slate-400">
        <input type="checkbox" checked={cleared} onChange={(e) => setCleared(e.target.checked)} />
        Cleared
      </label>
      {dirty && (
        <Button variant="secondary" disabled={busy} onClick={handleSave}>
          Save
        </Button>
      )}
    </div>
  )
}
