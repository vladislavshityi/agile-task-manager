import { createContext, useCallback, useContext, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getToken, setToken, subscribeToken } from '@/lib/auth-token'
import { qk } from '@/lib/query-keys'
import type { AuthResponse } from '@/types/api'

interface AuthContextValue {
  token: string | null
  signIn: (res: AuthResponse) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const token = useSyncExternalStore(subscribeToken, getToken)

  const signIn = useCallback(
    (res: AuthResponse) => {
      qc.clear()
      setToken(res.access_token)
      qc.setQueryData(qk.me, res.user)
    },
    [qc],
  )
  const signOut = useCallback(() => {
    setToken(null)
    qc.clear()
  }, [qc])

  const value = useMemo(() => ({ token, signIn, signOut }), [token, signIn, signOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
