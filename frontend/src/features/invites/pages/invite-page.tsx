import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError, errorMessage } from '@/lib/api-client'
import { ROLE_LABELS } from '@/lib/roles'
import { useAuth } from '@/features/auth/auth-context'
import { AuthLayout } from '@/features/auth/components/auth-layout'
import { useAcceptInvite, useInvitePreview } from '../hooks'

const CODE_MESSAGES: Record<string, string> = {
  invite_revoked: 'Это приглашение было отозвано.',
  invite_expired: 'Срок действия приглашения истёк.',
}

export default function InvitePage() {
  const { token = '' } = useParams()
  const { token: authToken } = useAuth()
  const navigate = useNavigate()
  const { data: preview, isLoading, error } = useInvitePreview(token)
  const accept = useAcceptInvite()
  const next = encodeURIComponent(`/invite/${token}`)

  const onAccept = () =>
    accept.mutate(token, {
      onSuccess: ({ workspace_id }) => {
        toast.success('Вы присоединились к пространству')
        navigate(`/w/${workspace_id}`, { replace: true })
      },
      onError: (e) =>
        toast.error(e instanceof ApiError && CODE_MESSAGES[e.code] ? CODE_MESSAGES[e.code] : errorMessage(e)),
    })

  if (isLoading) {
    return (
      <AuthLayout title="Приглашение" description="Загружаем…">
        <Skeleton className="h-24 rounded-xl" />
      </AuthLayout>
    )
  }

  if (error || !preview || !preview.valid) {
    return (
      <AuthLayout title="Приглашение недействительно" description="Ссылка устарела, отозвана или не существует.">
        <Button asChild className="w-full" size="lg">
          <Link to="/">На главную</Link>
        </Button>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      title={`Присоединиться к «${preview.workspace_name}»`}
      description={`${preview.inviter_name} приглашает вас как: ${ROLE_LABELS[preview.role].toLowerCase()}`}
    >
      {authToken ? (
        <Button size="lg" className="w-full" onClick={onAccept} disabled={accept.isPending}>
          Принять приглашение
        </Button>
      ) : (
        <div className="grid gap-2">
          <Button asChild size="lg">
            <Link to={`/login?next=${next}`}>Войти</Link>
          </Button>
          <Button asChild size="lg" variant="secondary">
            <Link to={`/register?next=${next}`}>Создать аккаунт</Link>
          </Button>
        </div>
      )}
    </AuthLayout>
  )
}
