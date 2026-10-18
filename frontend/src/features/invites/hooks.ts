import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { invitesApi, type InviteInput } from './api'

export function useInvites(wid: string, enabled = true) {
  return useQuery({ queryKey: qk.invites(wid), queryFn: () => invitesApi.list(wid), enabled })
}

export function useCreateInvite(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: InviteInput) => invitesApi.create(wid, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.invites(wid) }),
  })
}

export function useRevokeInvite(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => invitesApi.revoke(wid, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.invites(wid) }),
  })
}

export function useInvitePreview(token: string) {
  return useQuery({ queryKey: qk.invitePreview(token), queryFn: () => invitesApi.preview(token), retry: false })
}

export function useAcceptInvite() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: invitesApi.accept,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workspaces }),
  })
}
