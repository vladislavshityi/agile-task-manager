import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, UserMinus } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ConfirmDialog } from '@/components/confirm-dialog'
import { UserAvatar } from '@/components/user-avatar'
import { errorMessage } from '@/lib/api-client'
import { ROLE_LABELS, assignableRoles, isBelow } from '@/lib/roles'
import { useMe } from '@/features/auth/hooks'
import { useWorkspace } from '@/features/workspaces/workspace-context'
import type { Member, Role } from '@/types/api'
import { useMembers, useRemoveMember, useSetMemberRole } from '../hooks'

export function MembersTable() {
  const { id, role: myRole } = useWorkspace()
  const { data: me } = useMe()
  const navigate = useNavigate()
  const { data: members, isLoading } = useMembers(id)
  const setRole = useSetMemberRole(id)
  const removeMember = useRemoveMember(id)
  const [transfer, setTransfer] = useState<Member | null>(null)
  const [removing, setRemoving] = useState<Member | null>(null)

  const changeRole = (m: Member, role: Role) => {
    if (role === 'owner') return setTransfer(m)
    setRole.mutate({ userId: m.user.id, role }, { onError: (e) => toast.error(errorMessage(e)) })
  }

  if (isLoading) return <Skeleton className="h-40 rounded-2xl" />

  return (
    <>
      <div className="overflow-hidden rounded-2xl bg-card ring-1 ring-black/5 dark:ring-white/10">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Участник</TableHead>
              <TableHead>Роль</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {members?.map((m) => {
              const isMe = m.user.id === me?.id
              const canManage = !isMe && isBelow(m.role, myRole) && assignableRoles(myRole).length > 0
              const canLeave = isMe && m.role !== 'owner'
              return (
                <TableRow key={m.user.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <UserAvatar user={m.user} className="size-8" />
                      <div className="min-w-0">
                        <div className="truncate font-medium">
                          {m.user.full_name} {isMe && <span className="text-muted-foreground">(вы)</span>}
                        </div>
                        <div className="truncate text-xs text-muted-foreground">{m.user.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {canManage ? (
                      <Select value={m.role} onValueChange={(r) => changeRole(m, r as Role)}>
                        <SelectTrigger className="h-8 w-40 rounded-lg">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="rounded-xl">
                          {[...new Set([m.role, ...assignableRoles(myRole)])].map((r) => (
                            <SelectItem key={r} value={r} disabled={r === m.role}>
                              {ROLE_LABELS[r]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Badge variant="secondary">{ROLE_LABELS[m.role]}</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {canManage && (
                      <Button variant="ghost" size="icon" aria-label="Удалить участника" onClick={() => setRemoving(m)}>
                        <UserMinus className="size-4" />
                      </Button>
                    )}
                    {canLeave && (
                      <Button variant="ghost" size="icon" aria-label="Покинуть пространство" onClick={() => setRemoving(m)}>
                        <LogOut className="size-4" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
      <ConfirmDialog
        open={!!transfer}
        onOpenChange={(o) => !o && setTransfer(null)}
        title="Передать владение?"
        description={`${transfer?.user.full_name} станет владельцем пространства, а вы — администратором. Это действие нельзя отменить самостоятельно.`}
        confirmLabel="Передать"
        onConfirm={() =>
          transfer &&
          setRole.mutate(
            { userId: transfer.user.id, role: 'owner' },
            {
              onSuccess: () => toast.success('Владелец изменён'),
              onError: (e) => toast.error(errorMessage(e)),
            },
          )
        }
      />
      <ConfirmDialog
        open={!!removing}
        onOpenChange={(o) => !o && setRemoving(null)}
        title={removing?.user.id === me?.id ? 'Покинуть пространство?' : 'Удалить участника?'}
        description={
          removing?.user.id === me?.id
            ? 'Вы потеряете доступ ко всем доскам этого пространства.'
            : `${removing?.user.full_name} потеряет доступ к пространству, а его назначения на задачи будут сняты.`
        }
        confirmLabel={removing?.user.id === me?.id ? 'Покинуть' : 'Удалить'}
        onConfirm={() =>
          removing &&
          removeMember.mutate(removing.user.id, {
            onSuccess: () => {
              if (removing.user.id === me?.id) navigate('/', { replace: true })
            },
            onError: (e) => toast.error(errorMessage(e)),
          })
        }
      />
    </>
  )
}
