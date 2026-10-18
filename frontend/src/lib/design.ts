import type { Priority } from '@/types/api'

/** Apple system colors. */
export const APPLE_COLORS = [
  '#FF3B30',
  '#FF9500',
  '#FFCC00',
  '#34C759',
  '#007AFF',
  '#AF52DE',
  '#8E8E93',
] as const

export const PRIORITY_META: Record<Priority, { label: string; color: string }> = {
  low: { label: 'Низкий', color: '#8E8E93' },
  medium: { label: 'Средний', color: '#007AFF' },
  high: { label: 'Высокий', color: '#FF9500' },
  urgent: { label: 'Срочный', color: '#FF3B30' },
}

export const PRIORITIES: Priority[] = ['low', 'medium', 'high', 'urgent']

export function initials(name: string) {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join('') || '?'
  )
}
