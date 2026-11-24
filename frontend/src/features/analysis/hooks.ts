import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { analysisApi } from './api'
import type { AnalysisCreateInput } from '@/types/api'

export function useAnalyses(workspaceId: string) {
  return useQuery({ queryKey: qk.analyses(workspaceId), queryFn: () => analysisApi.list(workspaceId) })
}

export function useAnalysis(id: string) {
  return useQuery({ queryKey: qk.analysis(id), queryFn: () => analysisApi.get(id), enabled: !!id })
}

export function useCreateAnalysis(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: AnalysisCreateInput) => analysisApi.create(workspaceId, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: qk.analyses(workspaceId) }),
  })
}

export function useDeleteAnalysis(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => analysisApi.remove(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: qk.analysis(id) })
      void queryClient.invalidateQueries({ queryKey: qk.analyses(workspaceId) })
    },
  })
}
