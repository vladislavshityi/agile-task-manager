export const qk = {
  me: ['me'] as const,
  workspaces: ['workspaces'] as const,
  members: (wid: string) => ['workspaces', wid, 'members'] as const,
  invites: (wid: string) => ['workspaces', wid, 'invites'] as const,
  labels: (wid: string) => ['workspaces', wid, 'labels'] as const,
  boards: (wid: string) => ['workspaces', wid, 'boards'] as const,
  board: (id: string) => ['boards', id] as const,
  task: (id: string) => ['tasks', id] as const,
  myTasks: (wid: string, from?: string, to?: string) =>
    ['workspaces', wid, 'my-tasks', from ?? '', to ?? ''] as const,
  myTasksAll: (wid: string) => ['workspaces', wid, 'my-tasks'] as const,
  aiStatus: ['ai', 'status'] as const,
  invitePreview: (token: string) => ['invites', token] as const,
}
