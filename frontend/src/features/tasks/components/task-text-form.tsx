import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'
import type { TaskDetail } from '@/types/api'
import { useUpdateTask } from '../hooks'

const schema = z.object({
  title: z.string().trim().min(1, 'Введите название').max(200),
  description: z.string(),
})
type Values = z.infer<typeof schema>

/** Title + description, saved explicitly (other fields autosave). */
export function TaskTextForm({ task, readOnly }: { task: TaskDetail; readOnly: boolean }) {
  const update = useUpdateTask(task.id)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { title: task.title, description: task.description ?? '' },
  })

  useEffect(() => {
    reset({ title: task.title, description: task.description ?? '' })
  }, [task.id, task.updated_at, task.title, task.description, reset])

  const submit = handleSubmit((v) =>
    update.mutate(v, {
      onSuccess: () => toast.success('Сохранено'),
      onError: (e) => toast.error(errorMessage(e)),
    }),
  )

  return (
    <form onSubmit={submit} className="grid gap-3">
      <FormField label="Название" htmlFor="task-title" error={errors.title?.message}>
        <Input id="task-title" readOnly={readOnly} className="h-10 text-base font-medium" {...register('title')} />
      </FormField>
      <FormField label="Описание" htmlFor="task-desc">
        <Textarea
          id="task-desc"
          rows={5}
          readOnly={readOnly}
          placeholder={readOnly ? 'Нет описания' : 'Добавьте описание…'}
          {...register('description')}
        />
      </FormField>
      {!readOnly && isDirty && (
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={() => reset()}>
            Отменить
          </Button>
          <Button type="submit" disabled={update.isPending}>
            Сохранить
          </Button>
        </div>
      )}
    </form>
  )
}
