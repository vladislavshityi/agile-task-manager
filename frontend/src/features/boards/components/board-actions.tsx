import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { errorMessage } from '@/lib/api-client'
import { useDeleteBoard } from '../hooks'
import { BoardFormDialog } from './board-form-dialog'

interface Props {
  workspaceId: string
  board: { id: string; name: string; description: string }
}

export function BoardActions({ workspaceId, board }: Props) {
  const navigate = useNavigate()
  const remove = useDeleteBoard(workspaceId)
  const [editing, setEditing] = useState(false)
  const [deleting, setDeleting] = useState(false)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="icon" aria-label="Действия с доской">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="rounded-xl">
          <DropdownMenuItem onSelect={() => setEditing(true)}>
            <Pencil className="size-4" /> Редактировать
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onSelect={() => setDeleting(true)}>
            <Trash2 className="size-4" /> Удалить доску
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <BoardFormDialog workspaceId={workspaceId} board={board} open={editing} onOpenChange={setEditing} />
      <ConfirmDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={`Удалить доску «${board.name}»?`}
        description="Вместе с доской будут удалены все её колонки и задачи."
        onConfirm={() =>
          remove.mutate(board.id, {
            onSuccess: () => {
              toast.success('Доска удалена')
              navigate(`/w/${workspaceId}`, { replace: true })
            },
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </>
  )
}
