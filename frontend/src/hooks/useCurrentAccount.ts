// The backend has no "list accounts" endpoint (see backend/app/api/routes/accounts.py
// — only POST /accounts, GET/PATCH /accounts/{id}) and no auth/session concept, so
// there is no server-side notion of "which account is the user currently looking at."
// This hook tracks that choice client-side, in localStorage, so switching pages (My
// Account <-> Build Optimizer) keeps the same account selected without re-fetching an
// account list that doesn't exist.

import { useCallback, useEffect, useState } from 'react'

const STORAGE_KEY = 'archero2-optimizer:current-account-id'

function readStoredId(): number | null {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (raw === null) return null
  const parsed = Number(raw)
  return Number.isInteger(parsed) ? parsed : null
}

export function useCurrentAccount(): {
  accountId: number | null
  setAccountId: (id: number | null) => void
} {
  const [accountId, setAccountIdState] = useState<number | null>(() => readStoredId())

  useEffect(() => {
    function handleStorage(event: StorageEvent): void {
      if (event.key === STORAGE_KEY) {
        setAccountIdState(readStoredId())
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  const setAccountId = useCallback((id: number | null) => {
    if (id === null) {
      window.localStorage.removeItem(STORAGE_KEY)
    } else {
      window.localStorage.setItem(STORAGE_KEY, String(id))
    }
    setAccountIdState(id)
  }, [])

  return { accountId, setAccountId }
}
