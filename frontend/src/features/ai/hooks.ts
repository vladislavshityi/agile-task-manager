import { useMutation, useQuery } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { aiApi } from './api'

export function useAIStatus() {
  return useQuery({ queryKey: qk.aiStatus, queryFn: aiApi.status, staleTime: 30_000, retry: false })
}

/** True when the local model is installed and reachable. */
export function useAIAvailable() {
  return useAIStatus().data?.available ?? false
}

export function useGenerateTasks(boardId: string) {
  return useMutation({
    mutationFn: ({ prompt, count }: { prompt: string; count: number }) => aiApi.generateTasks(boardId, prompt, count),
  })
}

export function useSuggestDescription(taskId: string) {
  return useMutation({ mutationFn: () => aiApi.suggestDescription(taskId) })
}
