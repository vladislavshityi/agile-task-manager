import { api } from '@/lib/api-client'
import type { Invite, InvitePreview, Role } from '@/types/api'

export interface InviteInput {
  role?: Role
  expires_in_days?: number
}

export const invitesApi = {
  list: (wid: string) => api.get<Invite[]>(`/workspaces/${wid}/invites`),
  create: (wid: string, body: InviteInput) => api.post<Invite>(`/workspaces/${wid}/invites`, body),
  revoke: (wid: string, id: string) => api.delete(`/workspaces/${wid}/invites/${id}`),
  preview: (token: string) => api.get<InvitePreview>(`/invites/${token}`),
  accept: (token: string) => api.post<{ workspace_id: string }>(`/invites/${token}/accept`),
}
