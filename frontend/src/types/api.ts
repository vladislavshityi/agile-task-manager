// Mirrors SPEC.md "API" section exactly.

export type Role = 'owner' | 'admin' | 'member' | 'viewer'
export type Priority = 'low' | 'medium' | 'high' | 'urgent'

export interface User {
  id: string
  email: string
  full_name: string
  avatar_color: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  user: User
}

export interface Workspace {
  id: string
  name: string
  role: Role
  created_at: string
}

export interface Member {
  user: User
  role: Role
  joined_at: string
}

export interface Invite {
  id: string
  token: string
  role: Role
  created_at: string
  expires_at: string | null
  revoked: boolean
  created_by: User
}

export interface InvitePreview {
  workspace_name: string
  inviter_name: string
  role: Role
  valid: boolean
}

export interface Label {
  id: string
  workspace_id: string
  name: string
  color: string
}

export interface Task {
  id: string
  column_id: string
  title: string
  description: string
  priority: Priority
  due_date: string | null
  position: number
  created_at: string
  updated_at: string
  created_by: User
  assignees: User[]
  labels: Label[]
}

export interface Comment {
  id: string
  body: string
  created_at: string
  author: User
}

export interface TaskDetail extends Task {
  comments: Comment[]
}

export interface MyTask extends Task {
  board_id: string
  board_name: string
  column_name: string
}

export interface BoardSummary {
  id: string
  name: string
  description: string
  created_at: string
  task_count: number
}

export interface Column {
  id: string
  board_id: string
  name: string
  color: string
  position: number
  tasks: Task[]
}

export interface Board {
  id: string
  workspace_id: string
  name: string
  description: string
  columns: Column[]
}

export interface AIStatus {
  enabled: boolean
  available: boolean
  model: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface TaskDraft {
  title: string
  description: string
  priority: Priority
}

export interface WikiPageSummary {
  id: string
  parent_id: string | null
  title: string
  position: number
  updated_at: string
}

export interface WikiPage extends WikiPageSummary {
  workspace_id: string
  content: string
  created_at: string
  created_by: User
  updated_by: User
}

export interface ApiErrorBody {
  detail: string
  code: string
}

// Request payloads
export interface TaskInput {
  title: string
  description?: string
  priority?: Priority
  due_date?: string | null
  assignee_ids?: string[]
  label_ids?: string[]
}
export type TaskPatch = Partial<TaskInput>

export type AnalysisVisibility = 'private' | 'workspace'
export type AnalysisAccess = 'read' | 'edit' | 'manage'
export type FragmentKind = 'heading' | 'paragraph' | 'list_item'

export interface SpecFragment {
  id: string
  ordinal: number
  kind: FragmentKind
  section: string
  heading_path: string
  context: string
  text: string
  start: number
  end: number
}

export interface AnalysisMember {
  user: User
  can_edit: boolean
}

export interface AnalysisSummary {
  id: string
  workspace_id: string
  title: string
  visibility: AnalysisVisibility
  created_by: User
  created_at: string
  fragment_count: number
  access: AnalysisAccess
}

export interface Analysis extends AnalysisSummary {
  text: string
  fragments: SpecFragment[]
  members: AnalysisMember[]
}

export interface AnalysisCreateInput {
  title: string
  text: string
}
