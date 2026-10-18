import type { Role } from '@/types/api'

const RANK: Record<Role, number> = { viewer: 0, member: 1, admin: 2, owner: 3 }

export const ROLE_LABELS: Record<Role, string> = {
  owner: 'Владелец',
  admin: 'Администратор',
  member: 'Участник',
  viewer: 'Наблюдатель',
}

export function hasRole(role: Role, min: Role) {
  return RANK[role] >= RANK[min]
}

export function isBelow(a: Role, b: Role) {
  return RANK[a] < RANK[b]
}

/** Roles that `actor` may assign (SPEC: promote to admin / transfer ownership = owner only). */
export function assignableRoles(actor: Role): Role[] {
  if (actor === 'owner') return ['owner', 'admin', 'member', 'viewer']
  if (actor === 'admin') return ['member', 'viewer']
  return []
}
