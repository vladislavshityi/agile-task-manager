import { useState } from 'react'
import { Copy, Link2, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/empty-state'
import { errorMessage } from '@/lib/api-client'
import { formatLong } from '@/lib/dates'
import { ROLE_LABELS, assignableRoles } from '@/lib/roles'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { Role } from '@/types/api'
import { useCreateInvite, useInvites, useRevokeInvite } from '../hooks'

const EXPIRY_OPTIONS = [
  { value: '7', label: '7 дней' },
  { value: '30', label: '30 дней' },
  { value: 'never', label: 'Бессрочно' },
]

export function InvitesSection() {
  const { id, role: myRole } = useWorkspace()
  const { data: invites, isLoading } = useInvites(id)
  const create = useCreateInvite(id)
  const revoke = useRevokeInvite(id)
  // Invite role must be strictly below the creator's role.
  const roles = assignableRoles(myRole).filter((r) => r !== 'owner' && r !== myRole)
  const [role, setRole] = useState<Role>('member')
  const [expiry, setExpiry] = useState('7')

  const copy = async (token: string) => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/invite/${token}`)
      toast.success('Ссылка скопирована')
    } catch {
      toast.error('Не удалось скопировать ссылку')
    }
  }

  const submit = () =>
    create.mutate(
      { role, expires_in_days: expiry === 'never' ? undefined : Number(expiry) },
      {
        onSuccess: (inv) => {
          void copy(inv.token)
        },
        onError: (e) => toast.error(errorMessage(e)),
      },
    )

  return (
    <section className="grid gap-3">
      <div>
        <h3 className="font-semibold tracking-tight">Приглашения</h3>
        <p className="text-sm text-muted-foreground">Создайте ссылку и отправьте её тем, кого хотите пригласить.</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Select value={role} onValueChange={(v) => setRole(v as Role)}>
          <SelectTrigger className="w-44 rounded-xl">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="rounded-xl">
            {roles.map((r) => (
              <SelectItem key={r} value={r}>
                {ROLE_LABELS[r]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={expiry} onValueChange={setExpiry}>
          <SelectTrigger className="w-36 rounded-xl">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="rounded-xl">
            {EXPIRY_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button onClick={submit} disabled={create.isPending}>
          <Plus className="size-4" /> Создать ссылку
        </Button>
      </div>
      {isLoading && <Skeleton className="h-16 rounded-2xl" />}
      {invites?.length === 0 && <EmptyState icon={Link2} title="Активных приглашений нет" />}
      <ul className="grid gap-2">
        {invites?.map((inv) => (
          <li
            key={inv.id}
            className="flex items-center gap-3 rounded-2xl bg-card px-4 py-3 ring-1 ring-black/5 dark:ring-white/10"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Badge variant="secondary">{ROLE_LABELS[inv.role]}</Badge>
                <span className="truncate text-xs text-muted-foreground">
                  {inv.expires_at ? `до ${formatLong(inv.expires_at)}` : 'бессрочно'} · {inv.created_by.full_name}
                </span>
              </div>
              <code className="mt-1 block truncate text-xs text-muted-foreground">/invite/{inv.token}</code>
            </div>
            <Button variant="ghost" size="icon" aria-label="Скопировать ссылку" onClick={() => void copy(inv.token)}>
              <Copy className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Отозвать приглашение"
              onClick={() => revoke.mutate(inv.id, { onError: (e) => toast.error(errorMessage(e)) })}
            >
              <Trash2 className="size-4" />
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}
