import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { errorMessage } from '@/lib/api-client'
import { qk } from '@/lib/query-keys'
import type { Board, Column } from '@/types/api'
import { boardsApi, type BoardInput, type ColumnInput } from './api'

export function useBoards(wid: string) {
  return useQuery({ queryKey: qk.boards(wid), queryFn: () => boardsApi.list(wid) })
}

export function useBoard(id: string) {
  return useQuery({ queryKey: qk.board(id), queryFn: () => boardsApi.get(id) })
}

export function useCreateBoard(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: BoardInput) => boardsApi.create(wid, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.boards(wid) }),
  })
}

export function useUpdateBoard(wid: string, id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Partial<BoardInput>) => boardsApi.update(id, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: qk.boards(wid) })
      void qc.invalidateQueries({ queryKey: qk.board(id) })
    },
  })
}

export function useDeleteBoard(wid: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: boardsApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.boards(wid) }),
  })
}

export function useColumnMutations(boardId: string) {
  const qc = useQueryClient()
  const refresh = () => qc.invalidateQueries({ queryKey: qk.board(boardId) })
  return {
    create: useMutation({ mutationFn: (b: ColumnInput) => boardsApi.createColumn(boardId, b), onSuccess: refresh }),
    update: useMutation({
      mutationFn: ({ id, ...b }: ColumnInput & { id: string }) => boardsApi.updateColumn(id, b),
      onSuccess: refresh,
    }),
    remove: useMutation({ mutationFn: boardsApi.removeColumn, onSuccess: refresh }),
  }
}

/** Renumber positions contiguously after a local reorder. */
export function renumber(columns: Column[]): Column[] {
  return columns.map((c, ci) => ({
    ...c,
    position: ci,
    tasks: c.tasks.map((t, ti) => ({ ...t, column_id: c.id, position: ti })),
  }))
}

interface OptimisticVars<T> {
  columns: Column[]
  request: T
}

/**
 * Optimistic board update: write the new layout into the cache immediately,
 * roll back to the snapshot if the server rejects it.
 */
function useOptimisticBoard<T>(boardId: string, send: (req: T) => Promise<unknown>) {
  const qc = useQueryClient()
  const key = qk.board(boardId)
  return useMutation({
    mutationFn: ({ request }: OptimisticVars<T>) => send(request),
    onMutate: async ({ columns }) => {
      await qc.cancelQueries({ queryKey: key })
      const previous = qc.getQueryData<Board>(key)
      qc.setQueryData<Board>(key, (old) => (old ? { ...old, columns: renumber(columns) } : old))
      return { previous }
    },
    onError: (err, _vars, ctx) => {
      if (ctx?.previous) qc.setQueryData(key, ctx.previous)
      toast.error(errorMessage(err))
    },
    onSettled: () => qc.invalidateQueries({ queryKey: key }),
  })
}

export function useMoveTask(boardId: string) {
  return useOptimisticBoard<{ id: string; column_id: string; position: number }>(boardId, (r) =>
    boardsApi.moveTask(r.id, r.column_id, r.position),
  )
}

export function useMoveColumn(boardId: string) {
  return useOptimisticBoard<{ id: string; position: number }>(boardId, (r) =>
    boardsApi.moveColumn(r.id, r.position),
  )
}
