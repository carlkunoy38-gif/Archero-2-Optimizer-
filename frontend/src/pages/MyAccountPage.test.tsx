import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MyAccountPage } from './MyAccountPage'
import { api } from '../lib/apiClient'
import { useCurrentAccount } from '../hooks/useCurrentAccount'
import type { AccountDetailRead } from '../lib/types'

vi.mock('../lib/apiClient', () => ({
  api: {
    listHeroes: vi.fn(),
    listWeapons: vi.fn(),
    listArmor: vi.fn(),
    listRings: vi.fn(),
    listAmulets: vi.fn(),
    listPets: vi.fn(),
    listRunes: vi.fn(),
    listSkills: vi.fn(),
    listChapters: vi.fn(),
    createAccount: vi.fn(),
    getAccount: vi.fn(),
    updateAccount: vi.fn(),
    addHero: vi.fn(),
    updateHero: vi.fn(),
    removeHero: vi.fn(),
    activateHero: vi.fn(),
    deactivateHero: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    type: string
    status: number
    constructor(message: string, type = 'unknown_error', status = 500) {
      super(message)
      this.type = type
      this.status = status
    }
  },
}))

vi.mock('../hooks/useCurrentAccount', () => ({
  useCurrentAccount: vi.fn(),
}))

const mockedApi = vi.mocked(api)
const mockedUseCurrentAccount = vi.mocked(useCurrentAccount)

function emptyAccount(overrides: Partial<AccountDetailRead> = {}): AccountDetailRead {
  return {
    id: 1,
    display_name: 'carl',
    gold: 0,
    gems: 0,
    energy: 0,
    combat_power: 0,
    current_chapter_id: null,
    heroes: [],
    weapons: [],
    armor_pieces: [],
    rings: [],
    amulets: [],
    pets: [],
    runes: [],
    skill_selections: [],
    chapter_progress: [],
    ...overrides,
  }
}

function stubEmptyCatalogs() {
  mockedApi.listHeroes.mockResolvedValue([])
  mockedApi.listWeapons.mockResolvedValue([])
  mockedApi.listArmor.mockResolvedValue([])
  mockedApi.listRings.mockResolvedValue([])
  mockedApi.listAmulets.mockResolvedValue([])
  mockedApi.listPets.mockResolvedValue([])
  mockedApi.listRunes.mockResolvedValue([])
  mockedApi.listSkills.mockResolvedValue([])
  mockedApi.listChapters.mockResolvedValue([])
}

describe('MyAccountPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    stubEmptyCatalogs()
  })

  it('shows the account picker when no account is selected', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId: vi.fn() })

    render(<MyAccountPage />)

    expect(await screen.findByText('Create a new account')).toBeInTheDocument()
    expect(screen.getByText('Switch to an existing account')).toBeInTheDocument()
  })

  it('creates an account and adopts its id', async () => {
    const setAccountId = vi.fn()
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId })
    mockedApi.createAccount.mockResolvedValue({
      id: 5,
      display_name: 'carl',
      gold: 0,
      gems: 0,
      energy: 0,
      combat_power: 0,
      current_chapter_id: null,
    })

    const user = userEvent.setup()
    render(<MyAccountPage />)
    await screen.findByText('Create a new account')

    await user.type(screen.getByPlaceholderText('Display name'), 'carl')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() => expect(mockedApi.createAccount).toHaveBeenCalledWith({ display_name: 'carl' }))
    expect(setAccountId).toHaveBeenCalledWith(5)
  })

  it('shows the create error inline without adopting an account id', async () => {
    const setAccountId = vi.fn()
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId })
    mockedApi.createAccount.mockRejectedValue(new Error("Display name 'carl' is already taken"))

    const user = userEvent.setup()
    render(<MyAccountPage />)
    await screen.findByText('Create a new account')

    await user.type(screen.getByPlaceholderText('Display name'), 'carl')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByText("Display name 'carl' is already taken")).toBeInTheDocument()
    expect(setAccountId).not.toHaveBeenCalled()
  })

  it('verifies an account exists before switching to it', async () => {
    const setAccountId = vi.fn()
    mockedUseCurrentAccount.mockReturnValue({ accountId: null, setAccountId })
    mockedApi.getAccount.mockResolvedValue(emptyAccount({ id: 3 }))

    const user = userEvent.setup()
    render(<MyAccountPage />)
    await screen.findByText('Switch to an existing account')

    await user.type(screen.getByPlaceholderText('Account ID'), '3')
    await user.click(screen.getByRole('button', { name: 'Switch' }))

    await waitFor(() => expect(mockedApi.getAccount).toHaveBeenCalledWith(3))
    expect(setAccountId).toHaveBeenCalledWith(3)
  })

  it('renders the account detail and core stats once an account is selected', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.getAccount.mockResolvedValue(emptyAccount({ gold: 150, display_name: 'carl' }))

    render(<MyAccountPage />)

    expect(await screen.findByText('carl')).toBeInTheDocument()
    expect(screen.getByDisplayValue('150')).toBeInTheDocument()
  })

  it('adds a hero and refreshes the account afterward', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.listHeroes.mockResolvedValue([
      {
        id: 100,
        name: 'Test Hero',
        hero_class: 'warrior',
        rarity: 'epic',
        base_hp: 500,
        base_attack: 100,
        base_defense: 20,
        base_attack_speed: 1,
        signature_skill_description: null,
        description: null,
      },
    ])
    mockedApi.getAccount.mockResolvedValueOnce(emptyAccount()).mockResolvedValueOnce(
      emptyAccount({
        heroes: [{ id: 1, hero_id: 100, level: 1, stars: 0, is_active: false }],
      }),
    )
    mockedApi.addHero.mockResolvedValue({ id: 1, hero_id: 100, level: 1, stars: 0, is_active: false })

    const user = userEvent.setup()
    render(<MyAccountPage />)
    await screen.findByText('carl')

    const heroSelect = screen.getByText('Add heroes...').closest('select')
    if (!heroSelect) throw new Error('hero select not found')
    await user.selectOptions(heroSelect, 'Test Hero')
    await user.click(screen.getByRole('button', { name: 'Add' }))

    await waitFor(() => expect(mockedApi.addHero).toHaveBeenCalledWith(1, 100, 1, 0))
    await waitFor(() => expect(mockedApi.getAccount).toHaveBeenCalledTimes(2))
    expect(await screen.findByText('Test Hero')).toBeInTheDocument()
  })

  it('surfaces an error banner when a mutation fails', async () => {
    mockedUseCurrentAccount.mockReturnValue({ accountId: 1, setAccountId: vi.fn() })
    mockedApi.getAccount.mockResolvedValue(
      emptyAccount({ heroes: [{ id: 1, hero_id: 100, level: 1, stars: 0, is_active: false }] }),
    )
    mockedApi.listHeroes.mockResolvedValue([
      {
        id: 100,
        name: 'Test Hero',
        hero_class: 'warrior',
        rarity: 'epic',
        base_hp: 500,
        base_attack: 100,
        base_defense: 20,
        base_attack_speed: 1,
        signature_skill_description: null,
        description: null,
      },
    ])
    mockedApi.activateHero.mockRejectedValue(new Error('Hero 100 not found'))

    const user = userEvent.setup()
    render(<MyAccountPage />)
    await screen.findByText('Test Hero')

    await user.click(screen.getByRole('button', { name: 'Activate' }))

    expect(await screen.findByText('Hero 100 not found')).toBeInTheDocument()
  })
})
