import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'
import { useCreateBoard, useUpdateBoard } from '../hooks'

const schema = z.object({
  name: z.string().trim().min(1, 'Введите название').max(100),
  description: z.string().max(500),
})
type Values = z.infer<typeof schema>

interface Props {
  workspaceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  /** When provided, the dialog edits this board instead of creating one. */
  board?: { id: string; name: string; description: string }
}

export function BoardFormDialog({ workspaceId, open, onOpenChange, board }: Props) {
  const navigate = useNavigate()
  const create = useCreateBoard(workspaceId)
  const update = useUpdateBoard(workspaceId, board?.id ?? '')
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { name: '', description: '' } })

  useEffect(() => {
    if (open) reset({ name: board?.name ?? '', description: board?.description ?? '' })
  }, [open, board, reset])

  const submit = handleSubmit(async (values) => {
    const body = { name: values.name, description: values.description }
    try {
      if (board) {
        await update.mutateAsync(body)
        toast.success('Доска обновлена')
      } else {
        const created = await create.mutateAsync(body)
        toast.success('Доска создана')
        navigate(`/w/${workspaceId}/b/${created.id}`)
      }
      onOpenChange(false)
    } catch (err) {
      toast.error(errorMessage(err))
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl sm:max-w-md">
        <form onSubmit={submit} className="grid gap-4">
          <DialogHeader>
            <DialogTitle>{board ? 'Редактировать доску' : 'Новая доска'}</DialogTitle>
          </DialogHeader>
          <FormField label="Название" htmlFor="board-name" error={errors.name?.message}>
            <Input id="board-name" autoFocus autoComplete="off" {...register('name')} />
          </FormField>
          <FormField label="Описание" htmlFor="board-desc" error={errors.description?.message}>
            <Textarea id="board-desc" rows={3} {...register('description')} />
          </FormField>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {board ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
