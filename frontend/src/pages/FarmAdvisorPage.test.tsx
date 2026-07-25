import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { FarmAdvisorPage } from './FarmAdvisorPage'
import { api } from '../lib/apiClient'
import { useCurrentAccount } from '../hooks/useCurrentAccount'

vi.mock('../lib/apiClient', () => ({
  api: {
    adviseChapters: vi.fn(),
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
      <FarmAdvisorPage />
    </MemoryRouter>,
  )
}

describe('FarmAdvisorPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('points to My Account instead of requesting advice when no account is selected', () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId: vi.fn() })

    renderPage()

    expect(screen.getByRole('link', { name: 'My Account' })).toHaveAttribute('href', '/account')
    expect(mockedApi.adviseChapters).not.toHaveBeenCalled()
  })

  it('defaults to farm mode and renders the recommended chapter', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseChapters.mockResolvedValue({
      recommended_chapter_id: 18,
      ranking: [
        {
          chapter_id: 18,
          number: 18,
          name: 'Whispering Forest',
          score: 42.1,
          summary: 'Chapter 18 (Whispering Forest) is a safe, energy-efficient chapter to farm repeatedly.',
          reasons: ['Clear safety factor: 1.00 (0 = too risky, 1 = fully safe)'],
        },
      ],
    })

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() =>
      expect(mockedApi.adviseChapters).toHaveBeenCalledWith({ account_id: 1, objective: 'farm' }),
    )

    expect(
      await screen.findByText(
        'Chapter 18 (Whispering Forest) is a safe, energy-efficient chapter to farm repeatedly.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('Recommended')).toBeInTheDocument()
  })

  it('switches to progression mode when a non-farm mode is selected', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseChapters.mockResolvedValue({ recommended_chapter_id: 24, ranking: [] })

    const user = userEvent.setup()
    renderPage()

    await user.selectOptions(screen.getByLabelText('Mode'), 'balanced')
    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    await waitFor(() =>
      expect(mockedApi.adviseChapters).toHaveBeenCalledWith({
        account_id: 1,
        objective: 'balanced',
      }),
    )
  })

  it('shows the API error message when the chapter catalog is empty', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.adviseChapters.mockRejectedValue(new Error('No chapters in the catalog yet'))

    const user = userEvent.setup()
    renderPage()

    await user.click(screen.getByRole('button', { name: 'Get recommendation' }))

    expect(await screen.findByText('No chapters in the catalog yet')).toBeInTheDocument()
  })
})
