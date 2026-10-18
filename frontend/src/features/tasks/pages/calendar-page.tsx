import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameMonth,
  isToday,
  startOfMonth,
  startOfWeek,
} from 'date-fns'
import { ru } from 'date-fns/locale'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { PageHeader } from '@/components/page-header'
import { toApiDate } from '@/lib/dates'
import { PRIORITY_META } from '@/lib/design'
import { cn } from '@/lib/utils'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { MyTask } from '@/types/api'
import { useMyTasks } from '../hooks'

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MAX_PER_DAY = 3

export default function CalendarPage() {
  const { id } = useWorkspace()
  const navigate = useNavigate()
  const [month, setMonth] = useState(() => startOfMonth(new Date()))

  const days = useMemo(
    () =>
      eachDayOfInterval({
        start: startOfWeek(month, { weekStartsOn: 1 }),
        end: endOfWeek(endOfMonth(month), { weekStartsOn: 1 }),
      }),
    [month],
  )
  const range = { from: toApiDate(days[0]), to: toApiDate(days[days.length - 1]) }
  const { data: tasks, isLoading } = useMyTasks(id, range)

  const byDay = useMemo(() => {
    const map = new Map<string, MyTask[]>()
    for (const t of tasks ?? []) {
      if (!t.due_date) continue
      map.set(t.due_date, [...(map.get(t.due_date) ?? []), t])
    }
    return map
  }, [tasks])

  const open = (t: MyTask) => navigate(`/w/${id}/b/${t.board_id}?task=${t.id}`)

  return (
    <div className="mx-auto grid max-w-6xl gap-5">
      <PageHeader
        title={format(month, 'LLLL yyyy', { locale: ru })}
        description="Ваши задачи по срокам"
        actions={
          <>
            <Button variant="outline" onClick={() => setMonth(startOfMonth(new Date()))}>
              Сегодня
            </Button>
            <Button variant="outline" size="icon" aria-label="Предыдущий месяц" onClick={() => setMonth((m) => addMonths(m, -1))}>
              <ChevronLeft className="size-4" />
            </Button>
            <Button variant="outline" size="icon" aria-label="Следующий месяц" onClick={() => setMonth((m) => addMonths(m, 1))}>
              <ChevronRight className="size-4" />
            </Button>
          </>
        }
      />
      {isLoading ? (
        <Skeleton className="h-[32rem] rounded-2xl" />
      ) : (
        <div className="overflow-hidden rounded-2xl bg-card ring-1 ring-black/5 dark:ring-white/10">
          <div className="grid grid-cols-7 border-b border-black/5 text-center text-xs font-medium text-muted-foreground dark:border-white/10">
            {WEEKDAYS.map((d) => (
              <div key={d} className="py-2">
                {d}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {days.map((day) => {
              const key = toApiDate(day)
              const items = byDay.get(key) ?? []
              return (
                <div
                  key={key}
                  className={cn(
                    'min-h-24 border-r border-b border-black/5 p-1.5 last:border-r-0 dark:border-white/10',
                    !isSameMonth(day, month) && 'bg-muted/40 text-muted-foreground',
                  )}
                >
                  <span
                    className={cn(
                      'mb-1 inline-flex size-6 items-center justify-center rounded-full text-xs',
                      isToday(day) && 'bg-primary font-semibold text-primary-foreground',
                    )}
                  >
                    {format(day, 'd')}
                  </span>
                  <div className="grid gap-1">
                    {items.slice(0, MAX_PER_DAY).map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => open(t)}
                        title={t.title}
                        className="flex items-center gap-1 truncate rounded-md px-1.5 py-0.5 text-left text-xs transition-colors duration-150 hover:brightness-95"
                        style={{
                          backgroundColor: `${PRIORITY_META[t.priority].color}22`,
                          color: PRIORITY_META[t.priority].color,
                        }}
                      >
                        <span className="truncate font-medium">{t.title}</span>
                      </button>
                    ))}
                    {items.length > MAX_PER_DAY && (
                      <span className="px-1.5 text-xs text-muted-foreground">+{items.length - MAX_PER_DAY} ещё</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
