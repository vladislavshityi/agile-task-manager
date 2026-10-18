import { format, isBefore, isToday, parseISO, startOfDay } from 'date-fns'
import { ru } from 'date-fns/locale'

export const toApiDate = (d: Date) => format(d, 'yyyy-MM-dd')
export const fromApiDate = (s: string) => parseISO(s)
export const formatShort = (s: string) => format(parseISO(s), 'd MMM', { locale: ru })
export const formatLong = (s: string) => format(parseISO(s), 'd MMMM yyyy', { locale: ru })
export const formatDateTime = (s: string) => format(parseISO(s), 'd MMM, HH:mm', { locale: ru })

export type DueState = 'none' | 'overdue' | 'today' | 'upcoming'

export function dueState(due: string | null): DueState {
  if (!due) return 'none'
  const d = parseISO(due)
  if (isToday(d)) return 'today'
  return isBefore(d, startOfDay(new Date())) ? 'overdue' : 'upcoming'
}
