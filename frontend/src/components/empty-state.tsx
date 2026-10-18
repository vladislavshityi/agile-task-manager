import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface Props {
  icon: LucideIcon
  title: string
  action?: ReactNode
}

export function EmptyState({ icon: Icon, title, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-black/10 px-6 py-14 text-center dark:border-white/15">
      <div className="flex size-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
        <Icon className="size-6" />
      </div>
      <p className="max-w-xs text-sm text-muted-foreground">{title}</p>
      {action}
    </div>
  )
}
