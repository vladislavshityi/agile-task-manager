import { useState } from 'react'
import { ListPlus, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { Board } from '@/types/api'
import { useAIStatus } from '../hooks'
import { AIChatSheet } from './ai-chat-sheet'
import { GenerateTasksDialog } from './generate-tasks-dialog'

/** Board header buttons; hidden entirely when the server has the assistant switched off. */
export function BoardAIActions({ board, canEditTasks }: { board: Board; canEditTasks: boolean }) {
  const { data: status } = useAIStatus()
  const [chatOpen, setChatOpen] = useState(false)
  const [generateOpen, setGenerateOpen] = useState(false)

  if (!status?.enabled) return null

  return (
    <>
      {canEditTasks && (
        <Button variant="outline" onClick={() => setGenerateOpen(true)}>
          <ListPlus /> Задачи с ИИ
        </Button>
      )}
      <Button variant="outline" onClick={() => setChatOpen(true)}>
        <Sparkles /> Ассистент
      </Button>
      <AIChatSheet boardId={board.id} open={chatOpen} onOpenChange={setChatOpen} />
      {canEditTasks && <GenerateTasksDialog board={board} open={generateOpen} onOpenChange={setGenerateOpen} />}
    </>
  )
}
