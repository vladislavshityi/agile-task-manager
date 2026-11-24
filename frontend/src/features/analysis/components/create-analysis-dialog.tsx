import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { errorMessage } from '@/lib/api-client'
import { useCreateAnalysis } from '../hooks'

interface Props {
  workspaceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated?: (id: string) => void
}

export function CreateAnalysisDialog({ workspaceId, open, onOpenChange, onCreated }: Props) {
  const create = useCreateAnalysis(workspaceId)
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      setTitle('')
      setText('')
    }
    onOpenChange(nextOpen)
  }

  const submit = () => {
    if (!title.trim() || !text.trim()) return
    create.mutate(
      { title: title.trim(), text },
      {
        onSuccess: (analysis) => {
          toast.success('Анализ создан')
          handleOpenChange(false)
          onCreated?.(analysis.id)
        },
        onError: (error) => toast.error(errorMessage(error)),
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Новый анализ ТЗ</DialogTitle>
          <DialogDescription>Вставьте текст технического задания. После создания его текст нельзя изменить.</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название анализа" maxLength={200} />
          <Textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Текст технического задания"
            className="min-h-64 resize-y"
            maxLength={200000}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>Отмена</Button>
          <Button onClick={submit} disabled={create.isPending || !title.trim() || !text.trim()}>
            {create.isPending ? 'Анализируем…' : 'Создать анализ'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
