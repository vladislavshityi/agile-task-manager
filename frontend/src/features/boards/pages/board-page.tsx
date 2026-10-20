import { Link, useParams, useSearchParams } from 'react-router-dom'
import { SearchX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/empty-state'
import { PageHeader } from '@/components/page-header'
import { ApiError } from '@/lib/api-client'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import { TaskSheet } from '@/features/tasks/components/task-sheet'
import { BoardAIActions } from '@/features/ai/components/board-ai-actions'
import { BoardActions } from '../components/board-actions'
import { KanbanBoard } from '../components/kanban-board'
import { useBoard } from '../hooks'

function BoardSkeleton() {
  return (
    <div className="flex gap-3">
      {[0, 1, 2].map((i) => (
        <Skeleton key={i} className="h-72 w-72 shrink-0 rounded-2xl" />
      ))}
    </div>
  )
}

export default function BoardPage() {
  const { boardId = '' } = useParams()
  const { id: workspaceId, can } = useWorkspace()
  const [params, setParams] = useSearchParams()
  const { data: board, isLoading, error } = useBoard(boardId)
  const taskId = params.get('task')

  const openTask = (id: string | null) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (id) next.set('task', id)
        else next.delete('task')
        return next
      },
      { replace: !!taskId },
    )

  if (isLoading) {
    return (
      <div className="grid gap-6">
        <Skeleton className="h-10 w-64 rounded-xl" />
        <BoardSkeleton />
      </div>
    )
  }

  if (error || !board || board.workspace_id !== workspaceId) {
    const missing = error instanceof ApiError ? error.status === 404 : true
    return (
      <div className="mx-auto max-w-md pt-10">
        <EmptyState
          icon={SearchX}
          title={missing ? 'Доска не найдена' : 'Не удалось загрузить доску'}
          action={
            <Button asChild>
              <Link to={`/w/${workspaceId}`}>К доскам</Link>
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100svh-8.5rem)] flex-col gap-5">
      <PageHeader
        title={board.name}
        description={board.description}
        actions={
          <>
            {/* Keyed by board so the chat starts fresh on every board. */}
            <BoardAIActions key={board.id} board={board} canEditTasks={can('member')} />
            {can('admin') && <BoardActions workspaceId={workspaceId} board={board} />}
          </>
        }
      />
      <KanbanBoard
        board={board}
        canEditTasks={can('member')}
        canManage={can('admin')}
        onOpenTask={openTask}
      />
      <TaskSheet taskId={taskId} onClose={() => openTask(null)} />
    </div>
  )
}
