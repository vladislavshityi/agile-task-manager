import { Check, UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Skeleton } from '@/components/ui/skeleton'
import { UserAvatar } from '@/components/user-avatar'
import { useMembers } from '@/features/members/hooks'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { User } from '@/types/api'

interface Props {
  value: User[]
  disabled?: boolean
  onChange: (ids: string[]) => void
}

export function AssigneePicker({ value, disabled, onChange }: Props) {
  const { id } = useWorkspace()
  const { data: members, isLoading } = useMembers(id)
  const selected = new Set(value.map((u) => u.id))

  const toggle = (userId: string) => {
    const next = new Set(selected)
    if (next.has(userId)) next.delete(userId)
    else next.add(userId)
    onChange([...next])
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {value.map((u) => (
        <span key={u.id} className="inline-flex items-center gap-1.5 rounded-full bg-muted py-0.5 pr-2.5 pl-0.5 text-xs">
          <UserAvatar user={u} className="size-5" />
          {u.full_name}
        </span>
      ))}
      {!disabled && (
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="rounded-full">
              <UserPlus className="size-3.5" /> {value.length ? 'Изменить' : 'Назначить'}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="start" className="w-64 rounded-2xl p-1.5">
            {isLoading && <Skeleton className="h-16 rounded-xl" />}
            <div className="max-h-64 overflow-y-auto">
              {members?.map((m) => (
                <button
                  key={m.user.id}
                  type="button"
                  onClick={() => toggle(m.user.id)}
                  className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors duration-150 hover:bg-muted"
                >
                  <UserAvatar user={m.user} className="size-6" />
                  <span className="flex-1 truncate">{m.user.full_name}</span>
                  {selected.has(m.user.id) && <Check className="size-4 text-primary" />}
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      )}
      {disabled && value.length === 0 && <span className="text-sm text-muted-foreground">Не назначено</span>}
    </div>
  )
}
