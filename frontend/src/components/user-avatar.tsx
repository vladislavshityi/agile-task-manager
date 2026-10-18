import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { initials } from '@/lib/design'
import { cn } from '@/lib/utils'
import type { User } from '@/types/api'

interface Props {
  user: Pick<User, 'full_name' | 'avatar_color'>
  className?: string
}

export function UserAvatar({ user, className }: Props) {
  return (
    <Avatar className={cn('size-7', className)} title={user.full_name}>
      <AvatarFallback
        className="text-[11px] font-semibold text-white"
        style={{ backgroundColor: user.avatar_color }}
      >
        {initials(user.full_name)}
      </AvatarFallback>
    </Avatar>
  )
}
