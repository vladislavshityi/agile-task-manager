import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import { workspacesApi } from './api'

export function useWorkspaces() {
  return useQuery({ queryKey: qk.workspaces, queryFn: workspacesApi.list })
}

export function useCreateWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: workspacesApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workspaces }),
  })
}

export function useRenameWorkspace(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => workspacesApi.rename(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workspaces }),
  })
}

export function useDeleteWorkspace() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: workspacesApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.workspaces }),
  })
}
