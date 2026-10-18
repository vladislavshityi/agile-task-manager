import { useEffect, useRef, useState } from 'react'
import {
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  getFirstCollision,
  pointerWithin,
  rectIntersection,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { arrayMove, sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import type { Board, Column } from '@/types/api'
import { useMoveColumn, useMoveTask } from './hooks'

type Kind = 'task' | 'column'

const kindOf = (data: { current?: Record<string, unknown> } | undefined): Kind | undefined =>
  data?.current?.type as Kind | undefined

const columnOf = (cols: Column[], id: string | number) =>
  cols.find((c) => c.id === id) ?? cols.find((c) => c.tasks.some((t) => t.id === id))

const withTasks = (cols: Column[], columnId: string, tasks: Column['tasks']) =>
  cols.map((c) => (c.id === columnId ? { ...c, tasks } : c))

/**
 * Drag & drop state for the board. While dragging, the layout lives in local
 * state; on drop it is written to the query cache optimistically (see
 * useMoveTask / useMoveColumn) and the move endpoint is called.
 */
export function useBoardDnd(board: Board | undefined, boardId: string) {
  const moveTask = useMoveTask(boardId)
  const moveColumn = useMoveColumn(boardId)
  const [local, setLocal] = useState<Column[] | null>(null)
  const [active, setActive] = useState<{ kind: Kind; id: string } | null>(null)
  const dragging = useRef(false)
  const columns = local ?? board?.columns ?? []

  // Once the cache holds the dropped layout (or the server data changed), drop the local copy.
  useEffect(() => {
    if (!dragging.current) setLocal(null)
  }, [board])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const collisionDetection: CollisionDetection = (args) => {
      if (kindOf(args.active.data) === 'column') {
        return closestCenter({
          ...args,
          droppableContainers: args.droppableContainers.filter((c) => kindOf(c.data) === 'column'),
        })
      }
      const hits = pointerWithin(args)
      const pool = hits.length ? hits : rectIntersection(args)
      const overId = getFirstCollision(pool, 'id')
      if (overId == null) return []
      const col = columns.find((c) => c.id === overId)
      if (col && col.tasks.length > 0) {
        const taskIds = new Set(col.tasks.map((t) => t.id))
        const closest = closestCenter({
          ...args,
          droppableContainers: args.droppableContainers.filter((c) => taskIds.has(String(c.id))),
        })
        if (closest[0]) return [closest[0]]
      }
      return [{ id: overId }]
  }

  const onDragStart = (e: DragStartEvent) => {
    dragging.current = true
    setActive({ kind: kindOf(e.active.data) ?? 'task', id: String(e.active.id) })
  }

  const onDragOver = ({ active: a, over }: DragOverEvent) => {
    if (kindOf(a.data) !== 'task' || !over) return
    setLocal((prev) => {
      const cols = prev ?? board?.columns ?? []
      const from = columnOf(cols, a.id)
      const to = columnOf(cols, over.id)
      if (!from || !to || from.id === to.id) return prev
      const task = from.tasks.find((t) => t.id === a.id)
      if (!task) return prev
      const overIndex = to.tasks.findIndex((t) => t.id === over.id)
      let index = to.tasks.length
      if (overIndex >= 0) {
        const translated = a.rect.current.translated
        const below = translated ? translated.top > over.rect.top + over.rect.height / 2 : false
        index = overIndex + (below ? 1 : 0)
      }
      const nextTo = [...to.tasks.slice(0, index), task, ...to.tasks.slice(index)]
      return withTasks(
        withTasks(cols, from.id, from.tasks.filter((t) => t.id !== a.id)),
        to.id,
        nextTo,
      )
    })
  }

  const finish = () => {
    dragging.current = false
    setActive(null)
  }

  const onDragEnd = ({ active: a, over }: DragEndEvent) => {
    const kind = kindOf(a.data)
    finish()
    if (!over || !board) return setLocal(null)

    if (kind === 'column') {
      const from = columns.findIndex((c) => c.id === a.id)
      const to = columns.findIndex((c) => c.id === over.id)
      if (from < 0 || to < 0 || from === to) return setLocal(null)
      moveColumn.mutate({ columns: arrayMove(columns, from, to), request: { id: String(a.id), position: to } })
      return
    }

    let next = columns
    const cur = columnOf(columns, a.id)
    const overCol = columnOf(columns, over.id)
    if (cur && overCol && cur.id === overCol.id) {
      const oldIdx = cur.tasks.findIndex((t) => t.id === a.id)
      const overIdx = cur.tasks.findIndex((t) => t.id === over.id)
      const newIdx = overIdx >= 0 ? overIdx : cur.tasks.length - 1
      if (oldIdx !== newIdx) next = withTasks(columns, cur.id, arrayMove(cur.tasks, oldIdx, newIdx))
    }

    const dest = columnOf(next, a.id)
    const origin = columnOf(board.columns, a.id)
    if (!dest || !origin) return setLocal(null)
    const position = dest.tasks.findIndex((t) => t.id === a.id)
    const originPos = origin.tasks.findIndex((t) => t.id === a.id)
    if (dest.id === origin.id && position === originPos) return setLocal(null)
    moveTask.mutate({ columns: next, request: { id: String(a.id), column_id: dest.id, position } })
  }

  const onDragCancel = () => {
    finish()
    setLocal(null)
  }

  const activeTask =
    active?.kind === 'task' ? columns.flatMap((c) => c.tasks).find((t) => t.id === active.id) : undefined
  const activeColumn = active?.kind === 'column' ? columns.find((c) => c.id === active.id) : undefined

  return {
    columns,
    sensors,
    collisionDetection,
    activeTask,
    activeColumn,
    handlers: { onDragStart, onDragOver, onDragEnd, onDragCancel },
  }
}
