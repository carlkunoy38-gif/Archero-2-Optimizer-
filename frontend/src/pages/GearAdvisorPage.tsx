import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/apiClient'
import type { ArmorSlot, GearAdviceResponse, GearCategory, ObjectiveName } from '../lib/types'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import { Badge, Button, ErrorText, Panel, Select } from '../components/ui'

const OBJECTIVES: { value: ObjectiveName; label: string; hint: string }[] = [
  { value: 'balanced', label: 'Balanced', hint: 'A general-purpose blend of every dimension.' },
  { value: 'boss', label: 'Boss fight', hint: 'Weighs single-target damage output most.' },
  { value: 'farm', label: 'Farming', hint: 'Weighs clearing multiple enemies and resource gain most.' },
  { value: 'survival', label: 'Survival', hint: "Weighs your build's survivability most." },
]

const CATEGORIES: { value: GearCategory; label: string }[] = [
  { value: 'weapon', label: 'Weapon' },
  { value: 'armor', label: 'Armor' },
  { value: 'ring', label: 'Ring' },
  { value: 'amulet', label: 'Amulet' },
  { value: 'pet', label: 'Pet' },
]

const ARMOR_SLOTS: { value: ArmorSlot; label: string }[] = [
  { value: 'helmet', label: 'Helmet' },
  { value: 'chest', label: 'Chest' },
  { value: 'gloves', label: 'Gloves' },
  { value: 'boots', label: 'Boots' },
]

export function GearAdvisorPage() {
  const { accountId } = useCurrentAccount()
  const [category, setCategory] = useState<GearCategory>('weapon')
  const [armorSlot, setArmorSlot] = useState<ArmorSlot>('helmet')
  const [objective, setObjective] = useState<ObjectiveName>('balanced')
  const [result, setResult] = useState<GearAdviceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // A recommendation only ever matches the inputs it was computed for —
  // changing any of them makes the last result stale, so clear it rather
  // than risk it being mistaken for an answer to the new inputs.
  useEffect(() => {
    setResult(null)
    setError(null)
  }, [accountId, category, armorSlot, objective])

  async function handleAdvise() {
    if (accountId === null) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const response = await api.adviseGear({
        account_id: accountId,
        category,
        armor_slot: category === 'armor' ? armorSlot : undefined,
        objective,
      })
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  if (accountId === null) {
    return (
      <Panel>
        <p className="text-slate-300">
          No account selected yet. Go to{' '}
          <Link to="/account" className="text-violet-400 underline">
            My Account
          </Link>{' '}
          to create or switch to one first — the Gear Advisor compares gear you actually own.
        </p>
      </Panel>
    )
  }

  return (
    <div className="space-y-6">
      <Panel title="Gear Advisor">
        <p className="mb-4 text-sm text-slate-400">
          Compares every item account #{accountId} owns in one category (including whatever's
          currently equipped) and ranks them for the chosen objective — never a fixed tier list.
        </p>

        {error && <ErrorText>{error}</ErrorText>}

        <div className="mb-4 grid gap-4 sm:grid-cols-3">
          <div>
            <label htmlFor="gear-category" className="mb-1 block text-xs font-medium text-slate-400">
              Category
            </label>
            <Select
              id="gear-category"
              value={category}
              disabled={loading}
              onChange={(e) => setCategory(e.target.value as GearCategory)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </Select>
          </div>

          {category === 'armor' && (
            <div>
              <label htmlFor="gear-armor-slot" className="mb-1 block text-xs font-medium text-slate-400">
                Armor slot
              </label>
              <Select
                id="gear-armor-slot"
                value={armorSlot}
                disabled={loading}
                onChange={(e) => setArmorSlot(e.target.value as ArmorSlot)}
              >
                {ARMOR_SLOTS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </Select>
            </div>
          )}

          <div>
            <label htmlFor="gear-objective" className="mb-1 block text-xs font-medium text-slate-400">
              Objective
            </label>
            <Select
              id="gear-objective"
              value={objective}
              disabled={loading}
              onChange={(e) => setObjective(e.target.value as ObjectiveName)}
            >
              {OBJECTIVES.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          {OBJECTIVES.find((o) => o.value === objective)?.hint}
        </p>

        <Button disabled={loading} onClick={handleAdvise}>
          {loading ? 'Calculating...' : 'Get recommendation'}
        </Button>
      </Panel>

      {result && <ResultPanel result={result} />}
    </div>
  )
}

function ResultPanel({ result }: { result: GearAdviceResponse }) {
  return (
    <Panel title="Recommendation">
      <div className="space-y-3">
        {result.ranking.map((scored, index) => {
          const isRecommended = scored.catalog_id === result.recommended_catalog_id
          return (
            <div
              key={scored.catalog_id}
              className={`rounded-md border p-3 ${
                isRecommended ? 'border-emerald-600 bg-emerald-950/40' : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    #{index + 1} {scored.name}
                  </span>
                  {scored.is_currently_equipped && <Badge>Currently equipped</Badge>}
                  {isRecommended && <Badge tone="positive">Recommended</Badge>}
                </div>
                <span className="text-sm font-mono text-slate-400">
                  score {scored.score.toFixed(1)}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-300">{scored.summary}</p>
              <details className="mt-2">
                <summary className="cursor-pointer text-xs text-slate-500">Why (details)</summary>
                <ul className="mt-1 list-inside list-disc text-xs text-slate-400">
                  {scored.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </details>
            </div>
          )
        })}
      </div>
    </Panel>
  )
}
