import { api } from '@/lib/api-client'
import type { Member, Role } from '@/types/api'

export const membersApi = {
  list: (wid: string) => api.get<Member[]>(`/workspaces/${wid}/members`),
  setRole: (wid: string, userId: string, role: Role) =>
    api.patch<Member>(`/workspaces/${wid}/members/${userId}`, { role }),
  remove: (wid: string, userId: string) => api.delete(`/workspaces/${wid}/members/${userId}`),
}
