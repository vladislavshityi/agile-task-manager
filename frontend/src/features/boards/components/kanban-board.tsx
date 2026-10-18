import { DndContext, DragOverlay } from '@dnd-kit/core'
import { SortableContext, horizontalListSortingStrategy } from '@dnd-kit/sortable'
import { Columns3 } from 'lucide-react'
import { EmptyState } from '@/components/empty-state'
import type { Board } from '@/types/api'
import { useBoardDnd } from '../use-board-dnd'
import { AddColumn } from './add-column'
import { BoardColumn, ColumnPreview } from './board-column'
import { TaskCardView } from './task-card'

interface Props {
  board: Board
  canEditTasks: boolean
  canManage: boolean
  onOpenTask: (id: string) => void
}

export function KanbanBoard({ board, canEditTasks, canManage, onOpenTask }: Props) {
  const dnd = useBoardDnd(board, board.id)

  if (dnd.columns.length === 0 && !canManage) {
    return <EmptyState icon={Columns3} title="На этой доске пока нет колонок" />
  }

  return (
    <DndContext
      sensors={dnd.sensors}
      collisionDetection={dnd.collisionDetection}
      {...dnd.handlers}
    >
      <div className="flex min-h-0 flex-1 items-start gap-3 overflow-x-auto pb-3">
        <SortableContext items={dnd.columns.map((c) => c.id)} strategy={horizontalListSortingStrategy}>
          {dnd.columns.map((col) => (
            <BoardColumn
              key={col.id}
              column={col}
              boardId={board.id}
              canEditTasks={canEditTasks}
              canManage={canManage}
              onOpenTask={onOpenTask}
            />
          ))}
        </SortableContext>
        {canManage && <AddColumn boardId={board.id} />}
      </div>
      <DragOverlay dropAnimation={{ duration: 180, easing: 'ease-out' }}>
        {dnd.activeTask && <TaskCardView task={dnd.activeTask} dragging className="rotate-2" />}
        {dnd.activeColumn && <ColumnPreview column={dnd.activeColumn} />}
      </DragOverlay>
    </DndContext>
  )
}
