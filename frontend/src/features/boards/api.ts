import { api } from '@/lib/api-client'
import type { Board, BoardSummary, Column, Task } from '@/types/api'

export interface BoardInput {
  name: string
  description?: string | null
}
export interface ColumnInput {
  name?: string
  color?: string
}

export const boardsApi = {
  list: (wid: string) => api.get<BoardSummary[]>(`/workspaces/${wid}/boards`),
  get: (id: string) => api.get<Board>(`/boards/${id}`),
  create: (wid: string, body: BoardInput) => api.post<Board>(`/workspaces/${wid}/boards`, body),
  update: (id: string, body: Partial<BoardInput>) => api.patch<BoardSummary>(`/boards/${id}`, body),
  remove: (id: string) => api.delete(`/boards/${id}`),

  createColumn: (boardId: string, body: ColumnInput) => api.post<Column>(`/boards/${boardId}/columns`, body),
  updateColumn: (id: string, body: ColumnInput) => api.patch<Column>(`/columns/${id}`, body),
  moveColumn: (id: string, position: number) => api.post<Column>(`/columns/${id}/move`, { position }),
  removeColumn: (id: string) => api.delete(`/columns/${id}`),

  moveTask: (id: string, column_id: string, position: number) =>
    api.post<Task>(`/tasks/${id}/move`, { column_id, position }),
}
