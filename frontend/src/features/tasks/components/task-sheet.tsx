import { toast } from 'sonner'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { errorMessage } from '@/lib/api-client'
import { PRIORITIES, PRIORITY_META } from '@/lib/design'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { Priority, TaskDetail, TaskPatch } from '@/types/api'
import { useTask, useUpdateTask } from '../hooks'
import { AssigneePicker } from './assignee-picker'
import { DeleteTaskButton } from './delete-task-button'
import { DueDatePicker } from './due-date-picker'
import { LabelPicker } from './label-picker'
import { TaskComments } from './task-comments'
import { TaskTextForm } from './task-text-form'

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}

function TaskBody({ task, onClose }: { task: TaskDetail; onClose: () => void }) {
  const { can } = useWorkspace()
  const update = useUpdateTask(task.id)
  const canEdit = can('member')
  const patch = (p: TaskPatch) => update.mutate(p, { onError: (e) => toast.error(errorMessage(e)) })

  return (
    <div className="grid gap-5 px-4 pb-6">
      <TaskTextForm task={task} readOnly={!canEdit} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Row label="Приоритет">
          <Select value={task.priority} disabled={!canEdit} onValueChange={(v) => patch({ priority: v as Priority })}>
            <SelectTrigger className="h-9 w-full rounded-xl">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              {PRIORITIES.map((p) => (
                <SelectItem key={p} value={p}>
                  <span className="size-2 rounded-full" style={{ backgroundColor: PRIORITY_META[p].color }} />
                  {PRIORITY_META[p].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Row>
        <Row label="Срок">
          <DueDatePicker value={task.due_date} disabled={!canEdit} onChange={(due_date) => patch({ due_date })} />
        </Row>
      </div>
      <Row label="Исполнители">
        <AssigneePicker value={task.assignees} disabled={!canEdit} onChange={(assignee_ids) => patch({ assignee_ids })} />
      </Row>
      <Row label="Метки">
        <LabelPicker value={task.labels} disabled={!canEdit} onChange={(label_ids) => patch({ label_ids })} />
      </Row>
      <Separator />
      <TaskComments taskId={task.id} comments={task.comments} />
      {canEdit && (
        <>
          <Separator />
          <div>
            <DeleteTaskButton taskId={task.id} title={task.title} onDeleted={onClose} />
          </div>
        </>
      )}
    </div>
  )
}

interface Props {
  taskId: string | null
  onClose: () => void
}

/** Right-hand drawer with task details; open state is driven by the `?task=` URL param. */
export function TaskSheet({ taskId, onClose }: Props) {
  const { data: task, isLoading, isError } = useTask(taskId)

  return (
    <Sheet open={!!taskId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Задача</SheetTitle>
          <SheetDescription>{task ? `Создана ${task.created_by.full_name}` : 'Подробности задачи'}</SheetDescription>
        </SheetHeader>
        {isLoading && (
          <div className="grid gap-4 px-4">
            <Skeleton className="h-10 rounded-xl" />
            <Skeleton className="h-28 rounded-xl" />
            <Skeleton className="h-10 rounded-xl" />
          </div>
        )}
        {isError && <p className="px-4 text-sm text-muted-foreground">Не удалось загрузить задачу</p>}
        {task && <TaskBody task={task} onClose={onClose} />}
      </SheetContent>
    </Sheet>
  )
}
