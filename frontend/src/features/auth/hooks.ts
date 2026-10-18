import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { authApi } from './api'
import { useAuth } from './auth-context'

export function useMe() {
  const { token } = useAuth()
  return useQuery({ queryKey: qk.me, queryFn: authApi.me, enabled: !!token, staleTime: 5 * 60_000 })
}

export function useLogin() {
  const { signIn } = useAuth()
  return useMutation({ mutationFn: authApi.login, onSuccess: signIn })
}

export function useRegister() {
  const { signIn } = useAuth()
  return useMutation({ mutationFn: authApi.register, onSuccess: signIn })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: (user) => {
      qc.setQueryData(qk.me, user)
      void qc.invalidateQueries({ queryKey: ['workspaces'] })
    },
  })
}

export function useChangePassword() {
  return useMutation({ mutationFn: authApi.changePassword })
}
