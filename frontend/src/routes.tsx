import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { ProtectedRoute } from '@/features/auth/components/protected-route'
import LoginPage from '@/features/auth/pages/login-page'
import RegisterPage from '@/features/auth/pages/register-page'
import InvitePage from '@/features/invites/pages/invite-page'
import RootRedirect from '@/features/workspaces/pages/root-redirect'
import WorkspaceHomePage from '@/features/workspaces/pages/workspace-home-page'
import WorkspaceLayout from '@/features/workspaces/pages/workspace-layout'

const BoardPage = lazy(() => import('@/features/boards/pages/board-page'))
const MyTasksPage = lazy(() => import('@/features/tasks/pages/my-tasks-page'))
const CalendarPage = lazy(() => import('@/features/tasks/pages/calendar-page'))
const SettingsPage = lazy(() => import('@/features/settings/pages/settings-page'))

const lazyPage = (el: React.ReactNode) => <Suspense fallback={<Skeleton className="h-64 rounded-2xl" />}>{el}</Suspense>

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/invite/:token', element: <InvitePage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/', element: <RootRedirect /> },
      {
        path: '/w/:workspaceId',
        element: <WorkspaceLayout />,
        children: [
          { index: true, element: <WorkspaceHomePage /> },
          { path: 'b/:boardId', element: lazyPage(<BoardPage />) },
          { path: 'my-tasks', element: lazyPage(<MyTasksPage />) },
          { path: 'calendar', element: lazyPage(<CalendarPage />) },
          { path: 'settings', element: lazyPage(<SettingsPage />) },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
