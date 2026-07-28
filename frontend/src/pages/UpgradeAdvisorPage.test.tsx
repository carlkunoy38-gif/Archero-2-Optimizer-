import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { UpgradeAdvisorPage } from './UpgradeAdvisorPage'
import { api } from '../lib/apiClient'
import { useCurrentAccount } from '../hooks/useCurrentAccount'

vi.mock('../lib/apiClient', () => ({
  api: {
    adviseUpgrade: vi.fn(),
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
      <UpgradeAdvisorPage />
    </MemoryRouter>,
  )
}

describe('UpgradeAdvisorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('points to My Account instead of requesting advice when no account is selected', () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId: vi.fn() })

    renderPage()

    expect(screen.getByRole('link', { name: 'My Account' })).toHaveAttribute('href', '/account')
    expect(mockedApi.adviseUpgrade).not.toHaveBeenCalled()
  })

  it('requests upgrade advice for the selected account and objective', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseUpgrade.mockResolvedValue({
      recommended: { category: 'hero', ownership_id: 9, catalog_id: 5 },
      ranking: [
        {
          category: 'hero',
          ownership_id: 9,
          catalog_id: 5,
          name: 'Hero',
          from_level: 3,
          to_level: 5,
          gold_cost: 250,
          score: 8.7,
          summary: 'Spend 250 gold to upgrade Hero (level 3 -> 5): expected build improvement +8.7%.',
          reasons: ['Hero: level 3 -> 5 for 250 gold'],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await user.selectOptions(screen.getByLabelText('Objective'), 'farm')
    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() =>
      expect(mockedApi.adviseUpgrade).toHaveBeenCalledWith({ account_id: 1, objective: 'farm' }),
    )

    expect(
      await screen.findByText('Spend 250 gold to upgrade Hero (level 3 -> 5): expected build improvement +8.7%.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Recommended')).toBeInTheDocument()
    expect(screen.getByText('Level 3 → 5 for 250 gold')).toBeInTheDocument()
  })

  it('only marks the top-ranked item as recommended, even when a lower-ranked item from a different category shares the same catalog_id', async () => {
    // catalog_id is only unique *within* one category — a hero and a
    // weapon can both be catalog_id 1. Matching "recommended" by
    // catalog_id alone (instead of by ranking position) would wrongly
    // badge both.
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseUpgrade.mockResolvedValue({
      recommended: { category: 'hero', ownership_id: 3, catalog_id: 1 },
      ranking: [
        {
          category: 'hero',
          ownership_id: 3,
          catalog_id: 1,
          name: 'Test Hero',
          from_level: 10,
          to_level: 17,
          gold_cost: 4550,
          score: 41.6,
          summary: 'Spend 4550 gold to upgrade Test Hero (level 10 -> 17): expected build improvement +41.6%.',
          reasons: [],
        },
        {
          category: 'weapon',
          ownership_id: 4,
          catalog_id: 1,
          name: 'Dragon Bow',
          from_level: 10,
          to_level: 17,
          gold_cost: 4550,
          score: 5.1,
          summary: 'Spend 4550 gold to upgrade Dragon Bow (level 10 -> 17): expected build improvement +5.1%.',
          reasons: [],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await screen.findByText(
      'Spend 4550 gold to upgrade Dragon Bow (level 10 -> 17): expected build improvement +5.1%.',
    )
    expect(screen.getAllByText('Recommended')).toHaveLength(1)
  })

  it('shows the API error message when nothing is worth upgrading', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseUpgrade.mockRejectedValue(
      new Error('Account 1 has no upgrade worth making right now'),
    )

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    expect(
      await screen.findByText('Account 1 has no upgrade worth making right now'),
    ).toBeInTheDocument()
  })

  it('clears a stale recommendation when the objective changes afterward', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseUpgrade.mockResolvedValue({
      recommended: { category: 'hero', ownership_id: 9, catalog_id: 5 },
      ranking: [
        {
          category: 'hero',
          ownership_id: 9,
          catalog_id: 5,
          name: 'Hero',
          from_level: 3,
          to_level: 5,
          gold_cost: 250,
          score: 8.7,
          summary: 'Spend 250 gold to upgrade Hero (level 3 -> 5): expected build improvement +8.7%.',
          reasons: [],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))
    expect(
      await screen.findByText(
        'Spend 250 gold to upgrade Hero (level 3 -> 5): expected build improvement +8.7%.',
      ),
    ).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Objective'), 'farm')

    expect(
      screen.queryByText(
        'Spend 250 gold to upgrade Hero (level 3 -> 5): expected build improvement +8.7%.',
      ),
    ).not.toBeInTheDocument()
  })
})
