import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { NameDialog } from '@/components/name-dialog'
import { errorMessage } from '@/lib/api-client'
import { ROLE_LABELS } from '@/lib/roles'
import { useDeleteWorkspace, useRenameWorkspace } from '@/features/workspaces/hooks'
import { useWorkspace } from '@/features/workspaces/workspace-context'

export function WorkspaceTab() {
  const { workspace, can } = useWorkspace()
  const navigate = useNavigate()
  const rename = useRenameWorkspace(workspace.id)
  const remove = useDeleteWorkspace()
  const [renaming, setRenaming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const isOwner = can('owner')

  return (
    <div className="grid gap-4">
      <Card className="rounded-2xl border-0 ring-1 ring-black/5 dark:ring-white/10">
        <CardHeader>
          <CardTitle>{workspace.name}</CardTitle>
          <CardDescription>Ваша роль: {ROLE_LABELS[workspace.role]}</CardDescription>
        </CardHeader>
        {isOwner && (
          <CardContent>
            <Button variant="outline" onClick={() => setRenaming(true)}>
              Переименовать
            </Button>
          </CardContent>
        )}
      </Card>
      {isOwner && (
        <Card className="rounded-2xl border-0 ring-1 ring-destructive/30">
          <CardHeader>
            <CardTitle className="text-destructive">Удаление пространства</CardTitle>
            <CardDescription>Все доски, задачи и приглашения будут удалены безвозвратно.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="destructive" onClick={() => setDeleting(true)}>
              Удалить пространство
            </Button>
          </CardContent>
        </Card>
      )}
      <NameDialog
        open={renaming}
        onOpenChange={setRenaming}
        title="Переименовать пространство"
        initial={workspace.name}
        onSubmit={(name) => rename.mutateAsync(name)}
      />
      <ConfirmDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={`Удалить «${workspace.name}»?`}
        description="Это действие необратимо."
        onConfirm={() =>
          remove.mutate(workspace.id, {
            onSuccess: () => {
              toast.success('Пространство удалено')
              navigate('/', { replace: true })
            },
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </div>
  )
}
