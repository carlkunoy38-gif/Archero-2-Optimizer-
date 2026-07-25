import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/apiClient'
import type { ChapterAdviceResponse, ObjectiveName } from '../lib/types'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import { Badge, Button, ErrorText, Panel, Select } from '../components/ui'

const OBJECTIVES: { value: ObjectiveName; label: string; hint: string }[] = [
  {
    value: 'farm',
    label: 'Farm (repeatable)',
    hint: 'Ranks chapters by safe, energy-efficient repeatability — the best chapter to grind.',
  },
  {
    value: 'balanced',
    label: 'Progression',
    hint: 'Ranks chapters by the furthest one still safely reachable — the best chapter to push into next.',
  },
  { value: 'boss', label: 'Progression (boss-weighted)', hint: 'Progression mode, weighted for single-target power.' },
  { value: 'survival', label: 'Progression (survival-weighted)', hint: 'Progression mode, weighted for survivability.' },
]

export function FarmAdvisorPage() {
  const { accountId } = useCurrentAccount()
  const [objective, setObjective] = useState<ObjectiveName>('farm')
  const [result, setResult] = useState<ChapterAdviceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleAdvise() {
    if (accountId === null) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const response = await api.adviseChapters({ account_id: accountId, objective })
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
          to create or switch to one first — the Farm Advisor scores chapters against this
          account's actual combat power.
        </p>
      </Panel>
    )
  }

  return (
    <div className="space-y-6">
      <Panel title="Farm / Chapter Advisor">
        <p className="mb-4 text-sm text-slate-400">
          Recommends the best chapter to farm repeatedly, or the best chapter to push into next
          &mdash; and if account #{accountId} is under-powered for its next chapter, the best
          upgrade to make first.
        </p>

        {error && <ErrorText>{error}</ErrorText>}

        <div className="mb-4">
          <label htmlFor="farm-mode" className="mb-1 block text-xs font-medium text-slate-400">
            Mode
          </label>
          <Select
            id="farm-mode"
            value={objective}
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

function ResultPanel({ result }: { result: ChapterAdviceResponse }) {
  return (
    <Panel title="Recommendation">
      <div className="space-y-3">
        {result.ranking.map((scored, index) => {
          const isRecommended = scored.chapter_id === result.recommended_chapter_id
          return (
            <div
              key={scored.chapter_id}
              className={`rounded-md border p-3 ${
                isRecommended ? 'border-emerald-600 bg-emerald-950/40' : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    #{index + 1} Chapter {scored.number}: {scored.name}
                  </span>
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
