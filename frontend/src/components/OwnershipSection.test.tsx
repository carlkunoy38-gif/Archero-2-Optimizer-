import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { OwnershipSection } from './OwnershipSection'

describe('OwnershipSection', () => {
  it('labels the equip/unequip action as Activate/Deactivate for an "Active" section', async () => {
    const onEquip = vi.fn().mockResolvedValue(undefined)
    const onUnequip = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(
      <OwnershipSection
        title="Heroes"
        equippedLabel="Active"
        hasStarLevel={false}
        catalog={[{ id: 1, label: 'Test Hero' }]}
        entries={[{ ownershipId: 1, catalogId: 1, level: 1, starLevel: null, equipped: false }]}
        onAdd={vi.fn()}
        onUpdateLevel={vi.fn()}
        onRemove={vi.fn()}
        onEquip={onEquip}
        onUnequip={onUnequip}
        onError={vi.fn()}
      />,
    )

    // Not yet equipped: the action button reads "Activate", never "Active"
    // (a bare category label read as a button is ambiguous; see the fix
    // that came out of manually testing this component in the browser).
    expect(screen.queryByRole('button', { name: 'Active' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Activate' }))
    expect(onEquip).toHaveBeenCalledWith(1)
  })

  it('labels the unequip action as Deactivate, not "Unactive", once equipped', () => {
    render(
      <OwnershipSection
        title="Heroes"
        equippedLabel="Active"
        hasStarLevel={false}
        catalog={[{ id: 1, label: 'Test Hero' }]}
        entries={[{ ownershipId: 1, catalogId: 1, level: 1, starLevel: null, equipped: true }]}
        onAdd={vi.fn()}
        onUpdateLevel={vi.fn()}
        onRemove={vi.fn()}
        onEquip={vi.fn()}
        onUnequip={vi.fn()}
        onError={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: 'Deactivate' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Unactive' })).not.toBeInTheDocument()
  })

  it('only shows the Save button once the level/star fields are edited', async () => {
    const onUpdateLevel = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()

    render(
      <OwnershipSection
        title="Weapons"
        equippedLabel="Equipped"
        hasStarLevel={true}
        catalog={[{ id: 1, label: 'Dragon Bow' }]}
        entries={[{ ownershipId: 1, catalogId: 1, level: 1, starLevel: 0, equipped: false }]}
        onAdd={vi.fn()}
        onUpdateLevel={onUpdateLevel}
        onRemove={vi.fn()}
        onEquip={vi.fn()}
        onUnequip={vi.fn()}
        onError={vi.fn()}
      />,
    )

    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()

    const levelInput = screen.getByLabelText('Lvl', { exact: false })
    await user.clear(levelInput)
    await user.type(levelInput, '5')

    await user.click(screen.getByRole('button', { name: 'Save' }))
    expect(onUpdateLevel).toHaveBeenCalledWith(1, 5, 0)
  })

  it('reports errors from a failed action via onError', async () => {
    const onError = vi.fn()
    const user = userEvent.setup()

    render(
      <OwnershipSection
        title="Heroes"
        equippedLabel="Active"
        hasStarLevel={false}
        catalog={[{ id: 1, label: 'Test Hero' }]}
        entries={[{ ownershipId: 1, catalogId: 1, level: 1, starLevel: null, equipped: false }]}
        onAdd={vi.fn()}
        onUpdateLevel={vi.fn()}
        onRemove={vi.fn()}
        onEquip={vi.fn().mockRejectedValue(new Error('boom'))}
        onUnequip={vi.fn()}
        onError={onError}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Activate' }))

    expect(onError).toHaveBeenCalledWith('boom')
  })
})
