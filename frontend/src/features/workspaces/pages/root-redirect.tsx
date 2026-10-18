import { Navigate } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { useWorkspaces } from '../hooks'
import { readLastWorkspace } from '../last-workspace'

/** `/` → last visited workspace, else the first one. */
export default function RootRedirect() {
  const { data, isLoading } = useWorkspaces()
  if (isLoading) return <Skeleton className="m-6 h-40 rounded-2xl" />
  const target = data?.find((w) => w.id === readLastWorkspace()) ?? data?.[0]
  return target ? <Navigate to={`/w/${target.id}`} replace /> : <Navigate to="/login" replace />
}
