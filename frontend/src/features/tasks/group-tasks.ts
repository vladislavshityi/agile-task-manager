import { dueState, type DueState } from '@/lib/dates'
import type { MyTask } from '@/types/api'

export type TaskGroupKey = Exclude<DueState, 'none'> | 'none'

export const GROUP_META: { key: TaskGroupKey; title: string; accent?: string }[] = [
  { key: 'overdue', title: 'Просрочено', accent: '#FF3B30' },
  { key: 'today', title: 'Сегодня', accent: '#FF9500' },
  { key: 'upcoming', title: 'Предстоящие', accent: '#007AFF' },
  { key: 'none', title: 'Без срока' },
]

export function groupMyTasks(tasks: MyTask[]): Record<TaskGroupKey, MyTask[]> {
  const groups: Record<TaskGroupKey, MyTask[]> = { overdue: [], today: [], upcoming: [], none: [] }
  for (const t of tasks) groups[dueState(t.due_date)].push(t)
  const byDue = (a: MyTask, b: MyTask) => (a.due_date ?? '').localeCompare(b.due_date ?? '')
  groups.overdue.sort(byDue)
  groups.upcoming.sort(byDue)
  return groups
}
