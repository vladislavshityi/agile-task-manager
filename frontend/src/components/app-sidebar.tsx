import { useState } from 'react'
import { Link, useMatch } from 'react-router-dom'
import { BookOpen, CalendarDays, CheckSquare, Home, KanbanSquare, Plus, Settings } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  useSidebar,
} from '@/components/ui/sidebar'
import { WorkspaceSwitcher } from '@/features/workspaces/components/workspace-switcher'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import { useBoards } from '@/features/boards/hooks'
import { BoardFormDialog } from '@/features/boards/components/board-form-dialog'
import { UserMenu } from '@/components/user-menu'

function NavItem({ to, icon: Icon, label, end }: { to: string; icon: typeof Home; label: string; end?: boolean }) {
  const { isMobile, setOpenMobile } = useSidebar()
  const active = useMatch({ path: to, end: end ?? false }) !== null
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={active} className="rounded-xl">
        <Link to={to} onClick={() => isMobile && setOpenMobile(false)}>
          <Icon className="size-4" />
          <span>{label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}

export function AppSidebar() {
  const { id, can } = useWorkspace()
  const { data: boards, isLoading } = useBoards(id)
  const [creating, setCreating] = useState(false)
  const base = `/w/${id}`

  return (
    <Sidebar className="border-black/5 dark:border-white/10">
      <SidebarHeader className="p-3">
        <WorkspaceSwitcher />
      </SidebarHeader>
      <SidebarContent className="px-1">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <NavItem to={base} end icon={Home} label="Главная" />
              <NavItem to={`${base}/my-tasks`} icon={CheckSquare} label="Мои задачи" />
              <NavItem to={`${base}/calendar`} icon={CalendarDays} label="Календарь" />
              <NavItem to={`${base}/wiki`} icon={BookOpen} label="База знаний" />
              <NavItem to={`${base}/settings`} icon={Settings} label="Настройки" />
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Доски</SidebarGroupLabel>
          {can('admin') && (
            <SidebarGroupAction title="Новая доска" onClick={() => setCreating(true)}>
              <Plus className="size-4" />
            </SidebarGroupAction>
          )}
          <SidebarGroupContent>
            <SidebarMenu>
              {isLoading && [0, 1, 2].map((i) => <SidebarMenuSkeleton key={i} />)}
              {boards?.map((b) => (
                <NavItem key={b.id} to={`${base}/b/${b.id}`} icon={KanbanSquare} label={b.name} />
              ))}
              {boards?.length === 0 && (
                <p className="px-2 py-1 text-xs text-muted-foreground">Досок пока нет</p>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="p-3">
        <UserMenu />
      </SidebarFooter>
      <BoardFormDialog workspaceId={id} open={creating} onOpenChange={setCreating} />
    </Sidebar>
  )
}
