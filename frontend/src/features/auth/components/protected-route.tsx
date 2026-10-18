import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth-context'

export function ProtectedRoute() {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) {
    const next = location.pathname + location.search
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />
  }
  return <Outlet />
}
