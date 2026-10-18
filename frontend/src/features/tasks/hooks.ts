import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { qk } from '@/lib/query-keys'
import type { TaskInput, TaskPatch } from '@/types/api'
import { tasksApi, type LabelInput } from './api'

export function useTask(id: string | null) {
  return useQuery({ queryKey: qk.task(id ?? ''), queryFn: () => tasksApi.get(id!), enabled: !!id })
}

/** Any task change can affect the board it lives on and the "my tasks" lists. */
function useRefreshTaskViews() {
  const qc = useQueryClient()
  return (boardId?: string) => {
    if (boardId) void qc.invalidateQueries({ queryKey: qk.board(boardId) })
    else void qc.invalidateQueries({ queryKey: ['boards'] })
    void qc.invalidateQueries({ queryKey: ['workspaces'], predicate: (q) => q.queryKey[2] === 'my-tasks' })
    void qc.invalidateQueries({ queryKey: ['workspaces'], predicate: (q) => q.queryKey[2] === 'boards' })
  }
}

export function useCreateTask(boardId: string) {
  const refresh = useRefreshTaskViews()
  return useMutation({
    mutationFn: ({ columnId, ...body }: TaskInput & { columnId: string }) => tasksApi.create(columnId, body),
    onSuccess: () => refresh(boardId),
  })
}

export function useUpdateTask(id: string) {
  const qc = useQueryClient()
  const refresh = useRefreshTaskViews()
  return useMutation({
    mutationFn: (patch: TaskPatch) => tasksApi.update(id, patch),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.task(id) })
      refresh()
    },
  })
}

export function useDeleteTask() {
  const qc = useQueryClient()
  const refresh = useRefreshTaskViews()
  return useMutation({
    mutationFn: tasksApi.remove,
    onSuccess: (_d, id) => {
      qc.removeQueries({ queryKey: qk.task(id) })
      refresh()
    },
  })
}

export function useAddComment(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: string) => tasksApi.addComment(taskId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.task(taskId) }),
  })
}

export function useDeleteComment(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: tasksApi.removeComment,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.task(taskId) }),
  })
}

export function useMyTasks(wid: string, range?: { from: string; to: string }) {
  return useQuery({
    queryKey: qk.myTasks(wid, range?.from, range?.to),
    queryFn: () => tasksApi.mine({ workspace_id: wid, due_from: range?.from, due_to: range?.to }),
  })
}

export function useLabels(wid: string) {
  return useQuery({ queryKey: qk.labels(wid), queryFn: () => tasksApi.labels(wid) })
}

export function useCreateLabel(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: LabelInput) => tasksApi.createLabel(wid, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.labels(wid) }),
  })
}
