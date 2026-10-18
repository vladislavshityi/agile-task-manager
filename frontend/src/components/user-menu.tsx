import { useNavigate } from 'react-router-dom'
import { ChevronsUpDown, LogOut, Settings } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { UserAvatar } from '@/components/user-avatar'
import { useAuth } from '@/features/auth/auth-context'
import { useMe } from '@/features/auth/hooks'
import { useWorkspace } from '@/features/workspaces/workspace-context'

export function UserMenu() {
  const { data: me } = useMe()
  const { signOut } = useAuth()
  const { id } = useWorkspace()
  const navigate = useNavigate()

  if (!me) return <Skeleton className="h-12 w-full rounded-xl" />

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" className="rounded-xl">
              <UserAvatar user={me} className="size-8" />
              <div className="grid flex-1 text-left leading-tight">
                <span className="truncate text-sm font-medium">{me.full_name}</span>
                <span className="truncate text-xs text-muted-foreground">{me.email}</span>
              </div>
              <ChevronsUpDown className="size-4 text-muted-foreground" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-60 rounded-xl">
            <DropdownMenuLabel className="truncate">{me.email}</DropdownMenuLabel>
            <DropdownMenuItem onSelect={() => navigate(`/w/${id}/settings`)}>
              <Settings className="size-4" /> Профиль и настройки
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              variant="destructive"
              onSelect={() => {
                signOut()
                navigate('/login', { replace: true })
              }}
            >
              <LogOut className="size-4" /> Выйти
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
