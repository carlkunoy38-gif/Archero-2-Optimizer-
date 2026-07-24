import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/apiClient'
import type { ObjectiveName, SkillAdviceResponse, SkillRead } from '../lib/types'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import { Badge, Button, ErrorText, Panel, Select } from '../components/ui'

const OBJECTIVES: { value: ObjectiveName; label: string; hint: string }[] = [
  { value: 'balanced', label: 'Balanced', hint: 'A general-purpose blend of every dimension.' },
  { value: 'boss', label: 'Boss fight', hint: 'Weighs single-target damage output most.' },
  { value: 'farm', label: 'Farming', hint: 'Weighs clearing multiple enemies and resource gain most.' },
  { value: 'survival', label: 'Survival', hint: "Weighs your build's survivability most." },
]

export function BuildOptimizerPage() {
  const { accountId } = useCurrentAccount()
  const [skills, setSkills] = useState<SkillRead[] | null>(null)
  const [selectedSkillIds, setSelectedSkillIds] = useState<number[]>([])
  const [objective, setObjective] = useState<ObjectiveName>('balanced')
  const [result, setResult] = useState<SkillAdviceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listSkills()
      .then(setSkills)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  function toggleSkill(id: number) {
    setSelectedSkillIds((current) =>
      current.includes(id) ? current.filter((existing) => existing !== id) : [...current, id],
    )
  }

  async function handleAdvise() {
    if (accountId === null || selectedSkillIds.length === 0) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const response = await api.adviseSkills({
        account_id: accountId,
        candidate_skill_ids: selectedSkillIds,
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
          to create or switch to one first — the Skill Advisor scores candidates against a
          real account's build.
        </p>
      </Panel>
    )
  }

  return (
    <div className="space-y-6">
      <Panel title="Skill Advisor">
        <p className="mb-4 text-sm text-slate-400">
          Pick the skill choices the game offered you (account #{accountId}), and which
          objective matters right now. The recommendation is calculated from this account's
          actual current build — never a fixed tier list.
        </p>

        {error && <ErrorText>{error}</ErrorText>}

        <div className="mb-4">
          <label className="mb-1 block text-xs font-medium text-slate-400">Objective</label>
          <Select value={objective} onChange={(e) => setObjective(e.target.value as ObjectiveName)}>
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

        <div className="mb-4">
          <label className="mb-1 block text-xs font-medium text-slate-400">
            Candidate skills offered
          </label>
          {skills === null && <p className="text-sm text-slate-500">Loading skills...</p>}
          {skills !== null && skills.length === 0 && (
            <p className="text-sm text-slate-500">
              No skills in the catalog yet — nothing to pick from.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            {skills?.map((skill) => (
              <label
                key={skill.id}
                className={`cursor-pointer rounded-md border px-3 py-1.5 text-sm transition-colors ${
                  selectedSkillIds.includes(skill.id)
                    ? 'border-violet-500 bg-violet-950 text-violet-200'
                    : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-500'
                }`}
              >
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={selectedSkillIds.includes(skill.id)}
                  onChange={() => toggleSkill(skill.id)}
                />
                {skill.name}{' '}
                <span className="text-xs text-slate-500">
                  ({skill.skill_type}, tier {skill.tier})
                </span>
              </label>
            ))}
          </div>
        </div>

        <Button disabled={selectedSkillIds.length === 0 || loading} onClick={handleAdvise}>
          {loading ? 'Calculating...' : 'Get recommendation'}
        </Button>
      </Panel>

      {result && <ResultPanel result={result} />}
    </div>
  )
}

function ResultPanel({ result }: { result: SkillAdviceResponse }) {
  return (
    <Panel title="Recommendation">
      <div className="space-y-3">
        {result.ranking.map((scored, index) => {
          const isRecommended = scored.skill_id === result.recommended_skill_id
          return (
            <div
              key={scored.skill_id}
              className={`rounded-md border p-3 ${
                isRecommended ? 'border-emerald-600 bg-emerald-950/40' : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    #{index + 1} {scored.name}
                  </span>
                  <Badge>{scored.skill_type}</Badge>
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
