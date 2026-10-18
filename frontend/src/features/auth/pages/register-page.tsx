import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'
import { useAuth } from '../auth-context'
import { useRegister } from '../hooks'
import { AuthLayout, safeNext } from '../components/auth-layout'

const schema = z.object({
  full_name: z.string().trim().min(1, 'Введите имя'),
  email: z.string().email('Введите корректный email'),
  password: z.string().min(8, 'Минимум 8 символов'),
})
type Values = z.infer<typeof schema>

export default function RegisterPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const registerUser = useRegister()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema) })

  if (token && !registerUser.isPending && !registerUser.isSuccess) return <Navigate to={next} replace />

  const onSubmit = handleSubmit((values) =>
    registerUser.mutate(values, {
      onSuccess: () => navigate(next, { replace: true }),
      onError: (err) => setError('email', { message: errorMessage(err) }),
    }),
  )

  return (
    <AuthLayout title="Создать аккаунт" description="Это займёт меньше минуты">
      <form onSubmit={onSubmit} className="grid gap-4" noValidate>
        <FormField label="Имя" htmlFor="full_name" error={errors.full_name?.message}>
          <Input id="full_name" autoComplete="name" autoFocus {...register('full_name')} />
        </FormField>
        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register('email')} />
        </FormField>
        <FormField label="Пароль" htmlFor="password" error={errors.password?.message} hint="Минимум 8 символов">
          <Input id="password" type="password" autoComplete="new-password" {...register('password')} />
        </FormField>
        <Button type="submit" size="lg" disabled={registerUser.isPending}>
          {registerUser.isPending ? 'Создаём…' : 'Зарегистрироваться'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Уже есть аккаунт?{' '}
          <Link
            to={`/login${next !== '/' ? `?next=${encodeURIComponent(next)}` : ''}`}
            className="font-medium text-primary hover:underline"
          >
            Войти
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
