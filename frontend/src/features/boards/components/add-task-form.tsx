import { useState } from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { errorMessage } from '@/lib/api-client'
import { useCreateTask } from '@/features/tasks/hooks'

export function AddTaskForm({ boardId, columnId }: { boardId: string; columnId: string }) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const create = useCreateTask(boardId)

  const close = () => {
    setOpen(false)
    setTitle('')
  }

  const submit = () => {
    const value = title.trim()
    if (!value) return close()
    create.mutate(
      { columnId, title: value },
      {
        onSuccess: () => setTitle(''),
        onError: (e) => toast.error(errorMessage(e)),
      },
    )
  }

  if (!open) {
    return (
      <Button
        variant="ghost"
        size="sm"
        className="w-full justify-start text-muted-foreground"
        onClick={() => setOpen(true)}
      >
        <Plus className="size-4" /> Добавить задачу
      </Button>
    )
  }

  return (
    <div className="grid gap-2">
      <Textarea
        autoFocus
        rows={2}
        value={title}
        placeholder="Название задачи"
        className="resize-none rounded-xl bg-card"
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
          if (e.key === 'Escape') close()
        }}
      />
      <div className="flex gap-2">
        <Button size="sm" onClick={submit} disabled={create.isPending}>
          Добавить
        </Button>
        <Button size="sm" variant="ghost" onClick={close}>
          Закрыть
        </Button>
      </div>
    </div>
  )
}
