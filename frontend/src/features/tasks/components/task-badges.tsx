import { CalendarDays } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { dueState, formatShort } from '@/lib/dates'
import { PRIORITY_META } from '@/lib/design'
import { cn } from '@/lib/utils'
import type { Label, Priority } from '@/types/api'

export function PriorityDot({ priority, withLabel }: { priority: Priority; withLabel?: boolean }) {
  const meta = PRIORITY_META[priority]
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground" title={`Приоритет: ${meta.label}`}>
      <span className="size-2 rounded-full" style={{ backgroundColor: meta.color }} />
      {withLabel && meta.label}
    </span>
  )
}

export function DueBadge({ due }: { due: string | null }) {
  if (!due) return null
  const state = dueState(due)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs',
        state === 'overdue' && 'bg-[#FF3B30]/12 font-medium text-[#FF3B30]',
        state === 'today' && 'bg-[#FF9500]/15 font-medium text-[#FF9500]',
        (state === 'upcoming' || state === 'none') && 'text-muted-foreground',
      )}
    >
      <CalendarDays className="size-3" />
      {formatShort(due)}
    </span>
  )
}

export function LabelChip({ label }: { label: Pick<Label, 'name' | 'color'> }) {
  return (
    <Badge
      variant="secondary"
      className="h-5 rounded-md border-0 px-1.5 text-[11px] font-medium"
      style={{ backgroundColor: `${label.color}26`, color: label.color }}
    >
      {label.name}
    </Badge>
  )
}
