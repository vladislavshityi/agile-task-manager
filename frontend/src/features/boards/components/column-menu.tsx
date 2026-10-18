import { useState } from 'react'
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
import { ColorPicker } from '@/components/color-picker'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { NameDialog } from '@/components/name-dialog'
import { errorMessage } from '@/lib/api-client'
import type { Column } from '@/types/api'
import { useColumnMutations } from '../hooks'

export function ColumnMenu({ column }: { column: Column }) {
  const { update, remove } = useColumnMutations(column.board_id)
  const [renaming, setRenaming] = useState(false)
  const [deleting, setDeleting] = useState(false)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label="Действия с колонкой">
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="rounded-xl">
          <DropdownMenuItem onSelect={() => setRenaming(true)}>
            <Pencil className="size-4" /> Переименовать
          </DropdownMenuItem>
          <div className="px-2 py-2">
            <ColorPicker
              value={column.color}
              onChange={(color) =>
                update.mutate({ id: column.id, color }, { onError: (e) => toast.error(errorMessage(e)) })
              }
            />
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem variant="destructive" onSelect={() => setDeleting(true)}>
            <Trash2 className="size-4" /> Удалить
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <NameDialog
        open={renaming}
        onOpenChange={setRenaming}
        title="Переименовать колонку"
        initial={column.name}
        onSubmit={(name) => update.mutateAsync({ id: column.id, name })}
      />
      <ConfirmDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={`Удалить колонку «${column.name}»?`}
        description={`Все задачи в колонке (${column.tasks.length}) будут удалены без возможности восстановления.`}
        onConfirm={() =>
          remove.mutate(column.id, {
            onSuccess: () => toast.success('Колонка удалена'),
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </>
  )
}
