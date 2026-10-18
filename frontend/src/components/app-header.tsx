import { SidebarTrigger } from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/theme-toggle'
import { useWorkspace } from '@/features/workspaces/workspace-context'

export function AppHeader() {
  const { workspace } = useWorkspace()
  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b border-black/5 bg-background/70 px-4 backdrop-blur-xl dark:border-white/10">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mx-1 h-4" />
      <span className="truncate text-sm font-medium text-muted-foreground">{workspace.name}</span>
      <div className="ml-auto">
        <ThemeToggle />
      </div>
    </header>
  )
}
