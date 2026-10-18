import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { errorMessage } from '@/lib/api-client'
import { useDeleteTask } from '../hooks'

export function DeleteTaskButton({ taskId, title, onDeleted }: { taskId: string; title: string; onDeleted: () => void }) {
  const [open, setOpen] = useState(false)
  const remove = useDeleteTask()
  return (
    <>
      <Button variant="destructive" onClick={() => setOpen(true)}>
        <Trash2 className="size-4" /> Удалить задачу
      </Button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Удалить задачу?"
        description={`«${title}» будет удалена вместе с комментариями.`}
        onConfirm={() =>
          remove.mutate(taskId, {
            onSuccess: () => {
              toast.success('Задача удалена')
              onDeleted()
            },
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </>
  )
}
