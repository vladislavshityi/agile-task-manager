import { api } from '@/lib/api-client'
import type { Workspace } from '@/types/api'

export const workspacesApi = {
  list: () => api.get<Workspace[]>('/workspaces'),
  create: (name: string) => api.post<Workspace>('/workspaces', { name }),
  rename: (id: string, name: string) => api.patch<Workspace>(`/workspaces/${id}`, { name }),
  remove: (id: string) => api.delete(`/workspaces/${id}`),
}
