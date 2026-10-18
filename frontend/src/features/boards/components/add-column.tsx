import { useState } from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { errorMessage } from '@/lib/api-client'
import { useColumnMutations } from '../hooks'

export function AddColumn({ boardId }: { boardId: string }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const { create } = useColumnMutations(boardId)

  const close = () => {
    setOpen(false)
    setName('')
  }

  const submit = () => {
    const value = name.trim()
    if (!value) return close()
    create.mutate(
      { name: value },
      { onSuccess: close, onError: (e) => toast.error(errorMessage(e)) },
    )
  }

  if (!open) {
    return (
      <Button
        variant="secondary"
        className="h-10 w-72 shrink-0 justify-start rounded-2xl bg-black/5 text-muted-foreground hover:bg-black/10 dark:bg-white/10 dark:hover:bg-white/15"
        onClick={() => setOpen(true)}
      >
        <Plus className="size-4" /> Новая колонка
      </Button>
    )
  }

  return (
    <div className="grid h-fit w-72 shrink-0 gap-2 rounded-2xl bg-black/5 p-3 dark:bg-white/10">
      <Input
        autoFocus
        value={name}
        placeholder="Название колонки"
        className="rounded-xl bg-card"
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') submit()
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
