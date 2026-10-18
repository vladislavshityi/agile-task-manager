import { useEffect } from 'react'
import { Link, Outlet, useParams } from 'react-router-dom'
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'
import { EmptyState } from '@/components/empty-state'
import { ServerCrash } from 'lucide-react'
import { useWorkspaces } from '../hooks'
import { WorkspaceContext } from '../workspace-context'
import { LAST_WORKSPACE_KEY } from '../last-workspace'

export default function WorkspaceLayout() {
  const { workspaceId } = useParams()
  const { data: workspaces, isLoading, isError, refetch } = useWorkspaces()
  const workspace = workspaces?.find((w) => w.id === workspaceId)

  useEffect(() => {
    if (!workspace) return
    try {
      localStorage.setItem(LAST_WORKSPACE_KEY, workspace.id)
    } catch {
      /* ignore */
    }
  }, [workspace])

  if (isLoading) {
    return (
      <div className="flex min-h-svh gap-4 p-4">
        <Skeleton className="hidden h-full w-64 rounded-2xl md:block" />
        <Skeleton className="h-64 flex-1 rounded-2xl" />
      </div>
    )
  }

  if (isError || !workspace) {
    return (
      <div className="mx-auto flex min-h-svh max-w-md items-center">
        <EmptyState
          icon={ServerCrash}
          title={isError ? 'Не удалось загрузить рабочие пространства' : 'Пространство не найдено или у вас нет доступа'}
          action={
            isError ? (
              <Button onClick={() => void refetch()}>Повторить</Button>
            ) : (
              <Button asChild>
                <Link to="/">На главную</Link>
              </Button>
            )
          }
        />
      </div>
    )
  }

  return (
    <WorkspaceContext.Provider value={workspace}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="min-w-0 bg-transparent">
          <AppHeader />
          <div className="flex-1 p-4 md:p-6">
            <Outlet />
          </div>
        </SidebarInset>
      </SidebarProvider>
    </WorkspaceContext.Provider>
  )
}
