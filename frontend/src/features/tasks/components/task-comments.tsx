import { useState } from 'react'
import { Send, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { UserAvatar } from '@/components/user-avatar'
import { errorMessage } from '@/lib/api-client'
import { formatDateTime } from '@/lib/dates'
import { useMe } from '@/features/auth/hooks'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { Comment } from '@/types/api'
import { useAddComment, useDeleteComment } from '../hooks'

export function TaskComments({ taskId, comments }: { taskId: string; comments: Comment[] }) {
  const { can } = useWorkspace()
  const { data: me } = useMe()
  const [body, setBody] = useState('')
  const add = useAddComment(taskId)
  const remove = useDeleteComment(taskId)

  const submit = () => {
    const value = body.trim()
    if (!value) return
    add.mutate(value, {
      onSuccess: () => setBody(''),
      onError: (e) => toast.error(errorMessage(e)),
    })
  }

  return (
    <section className="grid gap-3">
      <h3 className="text-sm font-semibold">Комментарии {comments.length > 0 && `(${comments.length})`}</h3>
      {comments.length === 0 && <p className="text-sm text-muted-foreground">Пока нет комментариев</p>}
      <ul className="grid gap-3">
        {comments.map((c) => (
          <li key={c.id} className="group flex gap-2.5">
            <UserAvatar user={c.author} className="mt-0.5 size-7" />
            <div className="min-w-0 flex-1 rounded-xl bg-muted px-3 py-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{c.author.full_name}</span>
                <span>{formatDateTime(c.created_at)}</span>
                {(c.author.id === me?.id || can('admin')) && (
                  <button
                    type="button"
                    aria-label="Удалить комментарий"
                    className="ml-auto opacity-0 transition-opacity duration-150 group-hover:opacity-100 focus-visible:opacity-100"
                    onClick={() => remove.mutate(c.id, { onError: (e) => toast.error(errorMessage(e)) })}
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                )}
              </div>
              <p className="mt-0.5 text-sm break-words whitespace-pre-wrap">{c.body}</p>
            </div>
          </li>
        ))}
      </ul>
      {can('member') && (
        <div className="flex items-end gap-2">
          <Textarea
            rows={2}
            value={body}
            placeholder="Написать комментарий…"
            className="resize-none rounded-xl"
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
            }}
          />
          <Button size="icon-lg" aria-label="Отправить" onClick={submit} disabled={add.isPending || !body.trim()}>
            <Send className="size-4" />
          </Button>
        </div>
      )}
    </section>
  )
}
