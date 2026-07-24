import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { BuildOptimizerPage } from './BuildOptimizerPage'
import { api } from '../lib/apiClient'
import { useCurrentAccount } from '../hooks/useCurrentAccount'

vi.mock('../lib/apiClient', () => ({
  api: {
    listSkills: vi.fn(),
    adviseSkills: vi.fn(),
  },
  ApiError: class ApiError extends Error {},
}))

vi.mock('../hooks/useCurrentAccount', () => ({
  useCurrentAccount: vi.fn(),
}))

const mockedApi = vi.mocked(api)
const mockedUseCurrentAccount = vi.mocked(useCurrentAccount)

function renderPage() {
  return render(
    <MemoryRouter>
      <BuildOptimizerPage />
    </MemoryRouter>,
  )
}

describe('BuildOptimizerPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('points to My Account instead of requesting advice when no account is selected', () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId: vi.fn() })
    mockedApi.listSkills.mockResolvedValue([])

    renderPage()

    expect(screen.getByRole('link', { name: 'My Account' })).toHaveAttribute('href', '/account')
    expect(mockedApi.adviseSkills).not.toHaveBeenCalled()
  })

  it('loads candidate skills and requests a recommendation for the selected account', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.listSkills.mockResolvedValue([
      { id: 10, name: 'Multishot', skill_type: 'offensive', tier: 3, description: null, effects: [] },
      { id: 20, name: 'Iron Skin', skill_type: 'defensive', tier: 3, description: null, effects: [] },
    ])
    mockedApi.adviseSkills.mockResolvedValue({
      recommended_skill_id: 10,
      ranking: [
        {
          skill_id: 10,
          name: 'Multishot',
          skill_type: 'offensive',
          score: 40,
          summary: 'Multishot is the best pick.',
          reasons: ['Tier 3 baseline value: 30.0'],
        },
        {
          skill_id: 20,
          name: 'Iron Skin',
          skill_type: 'defensive',
          score: 30,
          summary: 'Iron Skin has no modeled effects yet.',
          reasons: ['Tier 3 baseline value: 30.0'],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await screen.findByText('Multishot', { exact: false })

    await user.click(screen.getByRole('checkbox', { name: /Multishot/ }))
    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() => expect(mockedApi.adviseSkills).toHaveBeenCalledWith({
      account_id: 1,
      candidate_skill_ids: [10],
      objective: 'balanced',
    }))

    expect(await screen.findByText('Multishot is the best pick.')).toBeInTheDocument()
    expect(screen.getByText('Recommended')).toBeInTheDocument()
  })

  it('disables the recommend button until at least one skill is selected', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.listSkills.mockResolvedValue([
      { id: 10, name: 'Multishot', skill_type: 'offensive', tier: 3, description: null, effects: [] },
    ])

    renderPage()
    await screen.findByText('Multishot', { exact: false })

    expect(screen.getByRole('button', { name: 'Get recommendation' })).toBeDisabled()
  })

  it('shows the API error message when the advise request fails', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.listSkills.mockResolvedValue([
      { id: 10, name: 'Multishot', skill_type: 'offensive', tier: 3, description: null, effects: [] },
    ])
    mockedApi.adviseSkills.mockRejectedValue(new Error('Skill 999999 not found'))

    const user = userEvent.setup()
    renderPage()
    await screen.findByText('Multishot', { exact: false })

    await user.click(screen.getByRole('checkbox', { name: /Multishot/ }))
    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    expect(await screen.findByText('Skill 999999 not found')).toBeInTheDocument()
  })
})
