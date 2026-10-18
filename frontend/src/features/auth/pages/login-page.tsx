import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'
import { useAuth } from '../auth-context'
import { useLogin } from '../hooks'
import { AuthLayout, safeNext } from '../components/auth-layout'

const schema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(1, 'Введите пароль'),
})
type Values = z.infer<typeof schema>

export default function LoginPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const login = useLogin()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) })

  if (token && !login.isPending && !login.isSuccess) return <Navigate to={next} replace />

  const onSubmit = handleSubmit((values) =>
    login.mutate(values, {
      onSuccess: () => navigate(next, { replace: true }),
      onError: (err) => setError('password', { message: errorMessage(err) }),
    }),
  )

  return (
    <AuthLayout title="С возвращением" description="Войдите, чтобы продолжить работу">
      <form onSubmit={onSubmit} className="grid gap-4" noValidate>
        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" autoFocus {...register('email')} />
        </FormField>
        <FormField label="Пароль" htmlFor="password" error={errors.password?.message}>
          <Input id="password" type="password" autoComplete="current-password" {...register('password')} />
        </FormField>
        <Button type="submit" size="lg" disabled={login.isPending}>
          {login.isPending ? 'Входим…' : 'Войти'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Нет аккаунта?{' '}
          <Link
            to={`/register${next !== '/' ? `?next=${encodeURIComponent(next)}` : ''}`}
            className="font-medium text-primary hover:underline"
          >
            Зарегистрироваться
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
