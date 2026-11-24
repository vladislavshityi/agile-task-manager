import { api } from '@/lib/api-client'
import type { Analysis, AnalysisCreateInput, AnalysisSummary } from '@/types/api'

export const analysisApi = {
  list: (workspaceId: string) => api.get<AnalysisSummary[]>(`/workspaces/${workspaceId}/analyses`),
  get: (id: string) => api.get<Analysis>(`/analyses/${id}`),
  create: (workspaceId: string, body: AnalysisCreateInput) =>
    api.post<Analysis>(`/workspaces/${workspaceId}/analyses`, body),
  remove: (id: string) => api.delete(`/analyses/${id}`),
}
