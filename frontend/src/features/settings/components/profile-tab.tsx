import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ColorPicker } from '@/components/color-picker'
import { FormField } from '@/components/form-field'
import { UserAvatar } from '@/components/user-avatar'
import { errorMessage } from '@/lib/api-client'
import { useChangePassword, useMe, useUpdateProfile } from '@/features/auth/hooks'

const profileSchema = z.object({ full_name: z.string().trim().min(1, 'Введите имя') })
const passwordSchema = z.object({
  current_password: z.string().min(1, 'Введите текущий пароль'),
  new_password: z.string().min(8, 'Минимум 8 символов'),
})

function ProfileForm() {
  const { data: me } = useMe()
  const update = useUpdateProfile()
  const [color, setColor] = useState(me?.avatar_color ?? '#007AFF')
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.infer<typeof profileSchema>>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: me?.full_name ?? '' },
  })

  if (!me) return null
  const submit = handleSubmit((v) =>
    update.mutate(
      { full_name: v.full_name, avatar_color: color },
      { onSuccess: () => toast.success('Профиль обновлён'), onError: (e) => toast.error(errorMessage(e)) },
    ),
  )

  return (
    <Card className="rounded-2xl border-0 ring-1 ring-black/5 dark:ring-white/10">
      <CardHeader>
        <CardTitle>Профиль</CardTitle>
        <CardDescription>{me.email}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid max-w-md gap-4">
          <div className="flex items-center gap-4">
            <UserAvatar user={{ full_name: me.full_name, avatar_color: color }} className="size-14 text-base" />
            <ColorPicker value={color} onChange={setColor} />
          </div>
          <FormField label="Имя" htmlFor="profile-name" error={errors.full_name?.message}>
            <Input id="profile-name" {...register('full_name')} />
          </FormField>
          <Button type="submit" className="w-fit" disabled={update.isPending}>
            Сохранить
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function PasswordForm() {
  const change = useChangePassword()
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<z.infer<typeof passwordSchema>>({ resolver: zodResolver(passwordSchema) })

  const submit = handleSubmit((v) =>
    change.mutate(v, {
      onSuccess: () => {
        toast.success('Пароль изменён')
        reset()
      },
      onError: (e) => setError('current_password', { message: errorMessage(e) }),
    }),
  )

  return (
    <Card className="rounded-2xl border-0 ring-1 ring-black/5 dark:ring-white/10">
      <CardHeader>
        <CardTitle>Пароль</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="grid max-w-md gap-4">
          <FormField label="Текущий пароль" htmlFor="cur-pass" error={errors.current_password?.message}>
            <Input id="cur-pass" type="password" autoComplete="current-password" {...register('current_password')} />
          </FormField>
          <FormField label="Новый пароль" htmlFor="new-pass" error={errors.new_password?.message}>
            <Input id="new-pass" type="password" autoComplete="new-password" {...register('new_password')} />
          </FormField>
          <Button type="submit" variant="secondary" className="w-fit" disabled={change.isPending}>
            Изменить пароль
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

export function ProfileTab() {
  return (
    <div className="grid gap-4">
      <ProfileForm />
      <PasswordForm />
    </div>
  )
}
