import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import type { Role } from '@/types/api'
import { membersApi } from './api'

export function useMembers(wid: string) {
  return useQuery({ queryKey: qk.members(wid), queryFn: () => membersApi.list(wid) })
}

export function useSetMemberRole(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: Role }) => membersApi.setRole(wid, userId, role),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.members(wid) })
      void qc.invalidateQueries({ queryKey: qk.workspaces })
    },
  })
}

export function useRemoveMember(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => membersApi.remove(wid, userId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.members(wid) })
      void qc.invalidateQueries({ queryKey: qk.workspaces })
    },
  })
}
