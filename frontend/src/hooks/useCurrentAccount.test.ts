import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { useCurrentAccount } from './useCurrentAccount'

describe('useCurrentAccount', () => {
  afterEach(() => {
    window.localStorage.clear()
  })

  it('starts with null when nothing is stored', () => {
    const { result } = renderHook(() => useCurrentAccount())
    expect(result.current.accountId).toBeNull()
  })

  it('persists the chosen id to localStorage and reflects it immediately', () => {
    const { result } = renderHook(() => useCurrentAccount())

    act(() => result.current.setAccountId(42))

    expect(result.current.accountId).toBe(42)
    expect(window.localStorage.getItem('archero2-optimizer:current-account-id')).toBe('42')
  })

  it('reads a previously stored id on mount', () => {
    window.localStorage.setItem('archero2-optimizer:current-account-id', '7')

    const { result } = renderHook(() => useCurrentAccount())

    expect(result.current.accountId).toBe(7)
  })

  it('clears storage when set to null', () => {
    const { result } = renderHook(() => useCurrentAccount())
    act(() => result.current.setAccountId(5))

    act(() => result.current.setAccountId(null))

    expect(result.current.accountId).toBeNull()
    expect(window.localStorage.getItem('archero2-optimizer:current-account-id')).toBeNull()
  })
})
