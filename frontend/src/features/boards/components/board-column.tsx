import type { HTMLAttributes, ReactNode } from 'react'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { cn } from '@/lib/utils'
import type { Column } from '@/types/api'
import { AddTaskForm } from './add-task-form'
import { ColumnMenu } from './column-menu'
import { SortableTaskCard, TaskCardView } from './task-card'

function ColumnFrame({ column, header, handleProps, children, className }: {
  column: Column
  header?: ReactNode
  handleProps?: HTMLAttributes<HTMLDivElement>
  children: ReactNode
  className?: string
}) {
  return (
    <section
      className={cn(
        'flex max-h-full w-72 shrink-0 flex-col rounded-2xl bg-black/[0.04] p-2 dark:bg-white/[0.07]',
        className,
      )}
      aria-label={column.name}
    >
      <div className="flex items-center gap-2 px-2 py-1.5">
        <div className={cn('flex min-w-0 flex-1 items-center gap-2', handleProps && 'cursor-grab')} {...handleProps}>
          <span className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: column.color }} />
          <h2 className="truncate text-sm font-semibold">{column.name}</h2>
        </div>
        <span className="text-xs text-muted-foreground tabular-nums">{column.tasks.length}</span>
        {header}
      </div>
      {children}
    </section>
  )
}

interface Props {
  column: Column
  boardId: string
  canEditTasks: boolean
  canManage: boolean
  onOpenTask: (id: string) => void
}

export function BoardColumn({ column, boardId, canEditTasks, canManage, onOpenTask }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: column.id,
    data: { type: 'column' },
    disabled: !canManage,
  })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn('flex max-h-full', isDragging && 'opacity-40')}
    >
      <ColumnFrame
        column={column}
        header={canManage ? <ColumnMenu column={column} /> : null}
        handleProps={canManage ? { ...attributes, ...listeners } : undefined}
      >
        <div className="min-h-0 flex-1 overflow-y-auto px-0.5 pt-1 pb-1">
          <SortableContext items={column.tasks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
            <div className="grid min-h-8 gap-2">
              {column.tasks.map((t) => (
                <SortableTaskCard key={t.id} task={t} disabled={!canEditTasks} onOpen={onOpenTask} />
              ))}
            </div>
          </SortableContext>
        </div>
        {canEditTasks && (
          <div className="pt-1">
            <AddTaskForm boardId={boardId} columnId={column.id} />
          </div>
        )}
      </ColumnFrame>
    </div>
  )
}

export function ColumnPreview({ column }: { column: Column }) {
  return (
    <ColumnFrame column={column} className="rotate-1 bg-card shadow-xl">
      <div className="grid gap-2 px-0.5 pt-1">
        {column.tasks.slice(0, 5).map((t) => (
          <TaskCardView key={t.id} task={t} />
        ))}
      </div>
    </ColumnFrame>
  )
}
