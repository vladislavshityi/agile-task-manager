import { api } from '@/lib/api-client'
import type { WikiPage, WikiPageSummary } from '@/types/api'

export interface WikiPageInput {
  title: string
  content?: string
  parent_id?: string | null
}

export const wikiApi = {
  list: (wid: string, q?: string) => api.get<WikiPageSummary[]>(`/workspaces/${wid}/wiki`, { q }),
  get: (id: string) => api.get<WikiPage>(`/wiki/${id}`),
  create: (wid: string, body: WikiPageInput) => api.post<WikiPage>(`/workspaces/${wid}/wiki`, body),
  update: (id: string, body: { title?: string; content?: string }) => api.patch<WikiPage>(`/wiki/${id}`, body),
  move: (id: string, parent_id: string | null, position: number) =>
    api.post<WikiPage>(`/wiki/${id}/move`, { parent_id, position }),
  remove: (id: string) => api.delete(`/wiki/${id}`),
}
