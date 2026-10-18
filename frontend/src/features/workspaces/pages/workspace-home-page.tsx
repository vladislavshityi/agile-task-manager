import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, KanbanSquare, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/empty-state'
import { PageHeader } from '@/components/page-header'
import { BoardFormDialog } from '@/features/boards/components/board-form-dialog'
import { useBoards } from '@/features/boards/hooks'
import { groupMyTasks } from '@/features/tasks/group-tasks'
import { useMyTasks } from '@/features/tasks/hooks'
import { DueBadge } from '@/features/tasks/components/task-badges'
import { useWorkspace } from '../workspace-context'

function MySummary() {
  const { id } = useWorkspace()
  const { data: tasks, isLoading } = useMyTasks(id)
  if (isLoading) return <Skeleton className="h-40 rounded-2xl" />
  const g = tasks ? groupMyTasks(tasks) : null
  const soon = g ? [...g.overdue, ...g.today, ...g.upcoming].slice(0, 5) : []

  return (
    <Card className="rounded-2xl border-0 ring-1 ring-black/5 dark:ring-white/10">
      <CardHeader>
        <CardTitle className="text-base">Назначено мне</CardTitle>
        <CardDescription>
          {g
            ? `Просрочено: ${g.overdue.length} · Сегодня: ${g.today.length} · Всего: ${tasks?.length ?? 0}`
            : 'Нет данных'}
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-1">
        {soon.length === 0 && <p className="text-sm text-muted-foreground">Ближайших задач со сроком нет</p>}
        {soon.map((t) => (
          <Link
            key={t.id}
            to={`/w/${id}/b/${t.board_id}?task=${t.id}`}
            className="flex items-center gap-3 rounded-xl px-2 py-1.5 text-sm transition-colors duration-150 hover:bg-muted"
          >
            <span className="flex-1 truncate font-medium">{t.title}</span>
            <span className="hidden text-xs text-muted-foreground sm:inline">{t.board_name}</span>
            <DueBadge due={t.due_date} />
          </Link>
        ))}
        <Button asChild variant="ghost" size="sm" className="mt-1 w-fit text-primary">
          <Link to={`/w/${id}/my-tasks`}>
            Все мои задачи <ArrowRight className="size-3.5" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}

export default function WorkspaceHomePage() {
  const { id, workspace, can } = useWorkspace()
  const { data: boards, isLoading } = useBoards(id)
  const [creating, setCreating] = useState(false)

  const newBoardButton = can('admin') && (
    <Button onClick={() => setCreating(true)}>
      <Plus className="size-4" /> Новая доска
    </Button>
  )

  return (
    <div className="mx-auto grid max-w-5xl gap-6">
      <PageHeader title={workspace.name} description="Доски пространства" actions={newBoardButton} />
      <MySummary />
      <section className="grid gap-3">
        <h2 className="text-sm font-semibold">Доски</h2>
        {isLoading && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-28 rounded-2xl" />
            ))}
          </div>
        )}
        {boards?.length === 0 && (
          <EmptyState
            icon={KanbanSquare}
            title={can('admin') ? 'Создайте первую доску, чтобы начать работу' : 'Администратор ещё не создал ни одной доски'}
            action={can('admin') && <Button onClick={() => setCreating(true)}>Создать доску</Button>}
          />
        )}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {boards?.map((b) => (
            <Link
              key={b.id}
              to={`/w/${id}/b/${b.id}`}
              className="group rounded-2xl bg-card p-4 ring-1 ring-black/5 transition-all duration-150 ease-out hover:-translate-y-0.5 hover:shadow-lg dark:ring-white/10"
            >
              <div className="flex items-center gap-2">
                <KanbanSquare className="size-4 text-primary" />
                <h3 className="truncate font-semibold tracking-tight">{b.name}</h3>
              </div>
              <p className="mt-1 line-clamp-2 min-h-10 text-sm text-muted-foreground">{b.description || 'Без описания'}</p>
              <p className="mt-2 text-xs text-muted-foreground">Задач: {b.task_count}</p>
            </Link>
          ))}
        </div>
      </section>
      <BoardFormDialog workspaceId={id} open={creating} onOpenChange={setCreating} />
    </div>
  )
}
