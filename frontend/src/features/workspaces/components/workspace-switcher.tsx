import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronsUpDown, Plus } from 'lucide-react'
import { toast } from 'sonner'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '@/components/ui/sidebar'
import { NameDialog } from '@/components/name-dialog'
import { ROLE_LABELS } from '@/lib/roles'
import { useCreateWorkspace, useWorkspaces } from '../hooks'
import { useWorkspace } from '../workspace-context'

export function WorkspaceSwitcher() {
  const { workspace } = useWorkspace()
  const { data: workspaces = [] } = useWorkspaces()
  const create = useCreateWorkspace()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton size="lg" className="rounded-xl">
                <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground">
                  {workspace.name.slice(0, 1).toUpperCase()}
                </div>
                <div className="grid flex-1 text-left leading-tight">
                  <span className="truncate text-sm font-semibold">{workspace.name}</span>
                  <span className="truncate text-xs text-muted-foreground">{ROLE_LABELS[workspace.role]}</span>
                </div>
                <ChevronsUpDown className="size-4 text-muted-foreground" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64 rounded-xl">
              <DropdownMenuLabel>Рабочие пространства</DropdownMenuLabel>
              {workspaces.map((w) => (
                <DropdownMenuItem key={w.id} onSelect={() => navigate(`/w/${w.id}`)}>
                  <span className="flex-1 truncate">{w.name}</span>
                  {w.id === workspace.id && <Check className="size-4 text-primary" />}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={() => setCreating(true)}>
                <Plus className="size-4" /> Создать пространство
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>
      <NameDialog
        open={creating}
        onOpenChange={setCreating}
        title="Новое пространство"
        description="Пространство объединяет доски и участников команды."
        submitLabel="Создать"
        onSubmit={async (name) => {
          const ws = await create.mutateAsync(name)
          toast.success('Пространство создано')
          navigate(`/w/${ws.id}`)
        }}
      />
    </>
  )
}
