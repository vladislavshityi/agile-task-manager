import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { UserAvatar } from '@/components/user-avatar'
import { cn } from '@/lib/utils'
import { DueBadge, LabelChip, PriorityDot } from '@/features/tasks/components/task-badges'
import type { Task } from '@/types/api'

/** Pure visual card; reused for the drag overlay. */
export function TaskCardView({ task, dragging, className }: { task: Task; dragging?: boolean; className?: string }) {
  return (
    <div
      className={cn(
        'rounded-xl bg-card p-3 text-sm ring-1 ring-black/5 transition-shadow duration-150 ease-out dark:ring-white/10',
        dragging && 'shadow-xl ring-primary/30',
        className,
      )}
    >
      {task.labels.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1">
          {task.labels.map((l) => (
            <LabelChip key={l.id} label={l} />
          ))}
        </div>
      )}
      <p className="font-medium leading-snug break-words">{task.title}</p>
      <div className="mt-2.5 flex items-center gap-2">
        <PriorityDot priority={task.priority} />
        <DueBadge due={task.due_date} />
        {task.assignees.length > 0 && (
          <div className="ml-auto flex -space-x-1.5">
            {task.assignees.slice(0, 3).map((u) => (
              <UserAvatar key={u.id} user={u} className="size-5 ring-2 ring-card" />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface Props {
  task: Task
  disabled: boolean
  onOpen: (id: string) => void
}

export function SortableTaskCard({ task, disabled, onOpen }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
    data: { type: 'task' },
    disabled,
  })
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn('touch-manipulation outline-none', isDragging && 'opacity-40')}
      {...attributes}
      {...listeners}
      onClick={() => onOpen(task.id)}
      onKeyDown={(e) => {
        listeners?.onKeyDown?.(e)
        if (e.key === 'Enter') onOpen(task.id)
      }}
    >
      <TaskCardView task={task} className={cn(!disabled && 'cursor-grab hover:ring-black/15 dark:hover:ring-white/25')} />
    </div>
  )
}
