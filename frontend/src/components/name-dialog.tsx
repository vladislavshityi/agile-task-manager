import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { FormField } from '@/components/form-field'
import { errorMessage } from '@/lib/api-client'

const schema = z.object({ name: z.string().trim().min(1, 'Введите название').max(100, 'Слишком длинное название') })
type Values = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  label?: string
  initial?: string
  submitLabel?: string
  onSubmit: (name: string) => Promise<unknown>
}

/** Small dialog with a single required name field. */
export function NameDialog({
  open,
  onOpenChange,
  title,
  description,
  label = 'Название',
  initial = '',
  submitLabel = 'Сохранить',
  onSubmit,
}: Props) {
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { name: initial } })

  useEffect(() => {
    if (open) reset({ name: initial })
  }, [open, initial, reset])

  const submit = handleSubmit(async ({ name }) => {
    try {
      await onSubmit(name)
      onOpenChange(false)
    } catch (err) {
      setError('name', { message: errorMessage(err) })
    }
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl sm:max-w-md">
        <form onSubmit={submit} className="grid gap-4">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>
          <FormField label={label} htmlFor="name-dialog-input" error={errors.name?.message}>
            <Input id="name-dialog-input" autoFocus autoComplete="off" {...register('name')} />
          </FormField>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
