import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GearAdvisorPage } from './GearAdvisorPage'
import { api } from '../lib/apiClient'
import { useCurrentAccount } from '../hooks/useCurrentAccount'

vi.mock('../lib/apiClient', () => ({
  api: {
    adviseGear: vi.fn(),
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
      <GearAdvisorPage />
    </MemoryRouter>,
  )
}

describe('GearAdvisorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('points to My Account instead of requesting advice when no account is selected', () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId: vi.fn() })

    renderPage()

    expect(screen.getByRole('link', { name: 'My Account' })).toHaveAttribute('href', '/account')
    expect(mockedApi.adviseGear).not.toHaveBeenCalled()
  })

  it('requests weapon advice by default and renders the ranking', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseGear.mockResolvedValue({
      recommended_catalog_id: 100,
      ranking: [
        {
          category: 'weapon',
          catalog_id: 100,
          name: 'Dragon Bow',
          is_currently_equipped: false,
          score: 92.3,
          summary: 'Dragon Bow is the strongest option.',
          reasons: ['raw attack: 100.00 -> 300.00 (+200.00)'],
        },
        {
          category: 'weapon',
          catalog_id: 200,
          name: 'Rusty Dagger',
          is_currently_equipped: true,
          score: 73.2,
          summary: 'Rusty Dagger has no measurable effect on your build yet.',
          reasons: ['currently equipped'],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() =>
      expect(mockedApi.adviseGear).toHaveBeenCalledWith({
        account_id: 1,
        category: 'weapon',
        armor_slot: undefined,
        objective: 'balanced',
      }),
    )

    expect(await screen.findByText('Dragon Bow is the strongest option.')).toBeInTheDocument()
    expect(screen.getByText('Recommended')).toBeInTheDocument()
    expect(screen.getByText('Currently equipped')).toBeInTheDocument()
  })

  it('includes an armor_slot only when the armor category is selected', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseGear.mockResolvedValue({ recommended_catalog_id: 1, ranking: [] })

    const user = userEvent.setup()
    renderPage()

    await user.selectOptions(screen.getByLabelText('Category'), 'armor')
    expect(screen.getByLabelText('Armor slot')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() =>
      expect(mockedApi.adviseGear).toHaveBeenCalledWith({
        account_id: 1,
        category: 'armor',
        armor_slot: 'helmet',
        objective: 'balanced',
      }),
    )
  })

  it('shows the API error message when the advise request fails', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseGear.mockRejectedValue(new Error('Account 1 owns no ring to compare'))

    const user = userEvent.setup()
    renderPage()

    await user.selectOptions(screen.getByLabelText('Category'), 'ring')
    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    expect(await screen.findByText('Account 1 owns no ring to compare')).toBeInTheDocument()
  })
})
