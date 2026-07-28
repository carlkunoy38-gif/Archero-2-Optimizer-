import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/apiClient'
import type { ObjectiveName, UpgradeAdviceResponse } from '../lib/types'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import { Badge, Button, ErrorText, Panel, Select } from '../components/ui'

const OBJECTIVES: { value: ObjectiveName; label: string; hint: string }[] = [
  { value: 'balanced', label: 'Balanced', hint: 'A general-purpose blend of every dimension.' },
  { value: 'boss', label: 'Boss fight', hint: 'Weighs single-target damage output most.' },
  { value: 'farm', label: 'Farming', hint: 'Weighs clearing multiple enemies and resource gain most.' },
  { value: 'survival', label: 'Survival', hint: "Weighs your build's survivability most." },
]

export function UpgradeAdvisorPage() {
  const { accountId } = useCurrentAccount()
  const [objective, setObjective] = useState<ObjectiveName>('balanced')
  const [result, setResult] = useState<UpgradeAdviceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // A recommendation only ever matches the inputs it was computed for —
  // changing any of them makes the last result stale, so clear it rather
  // than risk it being mistaken for an answer to the new inputs.
  useEffect(() => {
    setResult(null)
    setError(null)
  }, [accountId, objective])

  async function handleAdvise() {
    if (accountId === null) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const response = await api.adviseUpgrade({ account_id: accountId, objective })
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
          to create or switch to one first — the Upgrade Advisor spends this account's
          actual gold.
        </p>
      </Panel>
    )
  }

  return (
    <div className="space-y-6">
      <Panel title="Upgrade Advisor">
        <p className="mb-4 text-sm text-slate-400">
          Checks every hero/weapon/armor/ring/amulet/pet/rune account #{accountId} owns and
          finds the single best investment of its current gold — an upgrade that wouldn't
          actually improve the build is never recommended.
        </p>

        {error && <ErrorText>{error}</ErrorText>}

        <div className="mb-4">
          <label htmlFor="upgrade-objective" className="mb-1 block text-xs font-medium text-slate-400">
            Objective
          </label>
          <Select
            id="upgrade-objective"
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
          <p className="mt-1 text-xs text-slate-500">
            {OBJECTIVES.find((o) => o.value === objective)?.hint}
          </p>
        </div>

        <Button disabled={loading} onClick={handleAdvise}>
          {loading ? 'Calculating...' : 'Get recommendation'}
        </Button>
      </Panel>

      {result && <ResultPanel result={result} />}
    </div>
  )
}

function ResultPanel({ result }: { result: UpgradeAdviceResponse }) {
  return (
    <Panel title="Recommendation">
      <div className="space-y-3">
        {result.ranking.map((scored, index) => {
          // catalog_id is only unique *within* a category (hero id 1 and
          // weapon id 1 are different rows) — ranking[0] is always the
          // recommended one since the backend returns it pre-sorted, so
          // position is the only always-correct way to tell, unlike Gear
          // Advisor's single-category ranking where catalog_id alone works.
          const isRecommended = index === 0
          return (
            <div
              key={`${scored.category}-${scored.ownership_id}`}
              className={`rounded-md border p-3 ${
                isRecommended ? 'border-emerald-600 bg-emerald-950/40' : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    #{index + 1} {scored.name}
                  </span>
                  <Badge>{scored.category}</Badge>
                  {isRecommended && <Badge tone="positive">Recommended</Badge>}
                </div>
                <span className="text-sm font-mono text-slate-400">
                  {scored.score >= 0 ? '+' : ''}
                  {scored.score.toFixed(1)}%
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-300">{scored.summary}</p>
              <p className="mt-1 text-xs text-slate-500">
                Level {scored.from_level} &rarr; {scored.to_level} for {scored.gold_cost.toFixed(0)}{' '}
                gold
              </p>
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
