import { useNavigate } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { EmptyState } from '@/components/empty-state'
import { PageHeader } from '@/components/page-header'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { MyTask } from '@/types/api'
import { DueBadge, LabelChip, PriorityDot } from '../components/task-badges'
import { GROUP_META, groupMyTasks } from '../group-tasks'
import { useMyTasks } from '../hooks'

function TaskTable({ tasks, onOpen }: { tasks: MyTask[]; onOpen: (t: MyTask) => void }) {
  return (
    <div className="overflow-hidden rounded-2xl bg-card ring-1 ring-black/5 dark:ring-white/10">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Задача</TableHead>
            <TableHead className="hidden sm:table-cell">Доска</TableHead>
            <TableHead className="hidden md:table-cell">Статус</TableHead>
            <TableHead>Приоритет</TableHead>
            <TableHead className="text-right">Срок</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((t) => (
            <TableRow key={t.id} className="cursor-pointer" onClick={() => onOpen(t)}>
              <TableCell>
                <div className="font-medium">{t.title}</div>
                {t.labels.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {t.labels.map((l) => (
                      <LabelChip key={l.id} label={l} />
                    ))}
                  </div>
                )}
              </TableCell>
              <TableCell className="hidden text-muted-foreground sm:table-cell">{t.board_name}</TableCell>
              <TableCell className="hidden text-muted-foreground md:table-cell">{t.column_name}</TableCell>
              <TableCell>
                <PriorityDot priority={t.priority} withLabel />
              </TableCell>
              <TableCell className="text-right">
                <DueBadge due={t.due_date} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export default function MyTasksPage() {
  const { id, workspace } = useWorkspace()
  const navigate = useNavigate()
  const { data: tasks, isLoading } = useMyTasks(id)
  const open = (t: MyTask) => navigate(`/w/${id}/b/${t.board_id}?task=${t.id}`)
  const groups = tasks ? groupMyTasks(tasks) : null

  return (
    <div className="mx-auto grid max-w-5xl gap-6">
      <PageHeader title="Мои задачи" description={`Назначено вам в «${workspace.name}»`} />
      {isLoading && (
        <div className="grid gap-3">
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
        </div>
      )}
      {tasks?.length === 0 && <EmptyState icon={CheckCircle2} title="Все чисто — вам ничего не назначено" />}
      {groups &&
        GROUP_META.filter((g) => groups[g.key].length > 0).map((g) => (
          <section key={g.key} className="grid gap-2">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              {g.accent && <span className="size-2 rounded-full" style={{ backgroundColor: g.accent }} />}
              {g.title}
              <span className="font-normal text-muted-foreground">{groups[g.key].length}</span>
            </h2>
            <TaskTable tasks={groups[g.key]} onOpen={open} />
          </section>
        ))}
    </div>
  )
}
