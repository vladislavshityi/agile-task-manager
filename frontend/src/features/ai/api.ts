import { api, ApiError } from '@/lib/api-client'
import type { AIStatus, ChatMessage, TaskDraft } from '@/types/api'

type StreamEvent = { delta: string } | { done: true } | { error: string; code: string }

export const aiApi = {
  status: () => api.get<AIStatus>('/ai/status'),
  generateTasks: (boardId: string, prompt: string, count: number) =>
    api.post<{ tasks: TaskDraft[] }>(`/boards/${boardId}/ai/generate-tasks`, { prompt, count }),
  suggestDescription: (taskId: string) => api.post<{ description: string }>(`/tasks/${taskId}/ai/description`),

  /** Streams the assistant's reply; yields text deltas as they arrive. */
  async *chat(boardId: string, messages: ChatMessage[], signal?: AbortSignal): AsyncGenerator<string> {
    const res = await api.stream(`/boards/${boardId}/ai/chat`, { messages }, signal)
    if (!res.body) throw new ApiError(0, 'Пустой ответ сервера')
    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
    let buffer = ''
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += value
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.trim()) continue
        const event = JSON.parse(line) as StreamEvent
        if ('error' in event) throw new ApiError(502, event.error, event.code)
        if ('delta' in event) yield event.delta
      }
    }
  },
}
