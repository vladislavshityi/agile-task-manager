import { api } from '@/lib/api-client'
import type { Comment, Label, MyTask, Task, TaskDetail, TaskInput, TaskPatch } from '@/types/api'

export interface LabelInput {
  name: string
  color: string
}
export interface MyTasksParams {
  workspace_id: string
  due_from?: string
  due_to?: string
}

export const tasksApi = {
  get: (id: string) => api.get<TaskDetail>(`/tasks/${id}`),
  create: (columnId: string, body: TaskInput) => api.post<Task>(`/columns/${columnId}/tasks`, body),
  update: (id: string, body: TaskPatch) => api.patch<Task>(`/tasks/${id}`, body),
  remove: (id: string) => api.delete(`/tasks/${id}`),
  mine: (params: MyTasksParams) => api.get<MyTask[]>('/me/tasks', { ...params }),

  addComment: (taskId: string, body: string) => api.post<Comment>(`/tasks/${taskId}/comments`, { body }),
  removeComment: (id: string) => api.delete(`/comments/${id}`),

  labels: (wid: string) => api.get<Label[]>(`/workspaces/${wid}/labels`),
  createLabel: (wid: string, body: LabelInput) => api.post<Label>(`/workspaces/${wid}/labels`, body),
  updateLabel: (id: string, body: Partial<LabelInput>) => api.patch<Label>(`/labels/${id}`, body),
  removeLabel: (id: string) => api.delete(`/labels/${id}`),
}
