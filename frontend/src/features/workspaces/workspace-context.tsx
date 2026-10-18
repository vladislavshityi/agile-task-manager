import { createContext, useContext } from 'react'
import { hasRole } from '@/lib/roles'
import type { Role, Workspace } from '@/types/api'

export const WorkspaceContext = createContext<Workspace | null>(null)

/** Current workspace (from the route) plus role helpers. */
export function useWorkspace() {
  const ws = useContext(WorkspaceContext)
  if (!ws) throw new Error('useWorkspace must be used inside WorkspaceLayout')
  return {
    workspace: ws,
    id: ws.id,
    role: ws.role,
    can: (min: Role) => hasRole(ws.role, min),
  }
}
