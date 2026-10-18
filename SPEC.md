# Agile Task Manager — specification

This document is the contract between backend and frontend. Change it deliberately and keep both sides in sync.

## Stack

| Layer    | Choice |
|----------|--------|
| Backend  | Python 3.12, FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, pydantic-settings, PyJWT, pwdlib[argon2]. Package manager: **uv** |
| DB       | PostgreSQL 16 (docker compose) |
| Frontend | Vite, React 19, TypeScript (strict), Tailwind CSS v4, shadcn/ui, TanStack Query, React Router, dnd-kit, react-hook-form + zod, sonner, lucide-react |
| Infra    | docker compose: `db`, `backend`, `frontend` (nginx serving the build, proxying `/api`) |

## Repository layout

```
agile-task-manager/
  backend/
    pyproject.toml, uv.lock, alembic.ini, Dockerfile
    alembic/versions/0001_initial.py
    src/app/
      main.py                 # app factory, router registration, exception handlers
      core/                   # config.py, db.py, security.py, errors.py, deps.py
      modules/
        auth/                 # router, service, schemas
        users/                # models, schemas, repository, service, router
        workspaces/           # workspaces + members + invites
        boards/               # boards + columns
        tasks/                # tasks + assignees + comments + labels
    tests/                    # pytest, real Postgres, transaction rollback per test
  frontend/
    src/
      components/ui/          # shadcn components (generated)
      components/             # app shell: sidebar, header, theme toggle
      features/<feature>/     # api.ts, hooks.ts, components/*, pages/*
      lib/                    # api-client.ts, utils.ts, query-client.ts
      routes.tsx
  docker-compose.yml
  .env.example
  README.md
```

Each backend module: `models.py` (ORM) → `repository.py` (queries only) → `service.py`
(business rules, permission checks, raises domain errors) → `router.py` (thin: parse, call
service, return schema). No HTTP concepts below the router layer.

## Domain model

- **User**: id (uuid), email (unique, lowercase), password_hash, full_name, avatar_color (hex), created_at
- **Workspace**: id (uuid), name, created_at. Every user gets a personal workspace on registration (role `owner`).
- **Membership**: (workspace_id, user_id) PK, role ∈ `owner | admin | member | viewer`, created_at
- **Invite**: id, workspace_id, token (unique, urlsafe), role (default `member`), created_by, created_at, expires_at (nullable), revoked (bool)
- **Board**: id (uuid), workspace_id, name, description, created_at
- **Column**: id (uuid), board_id, name, color (hex string, default `#8E8E93`), position (int)
- **Task**: id (uuid), column_id, title, description, priority ∈ `low | medium | high | urgent` (default `medium`), due_date (date, nullable), position (int), created_by, created_at, updated_at
- **TaskAssignee**: (task_id, user_id) PK
- **Label**: id, workspace_id, name, color. **TaskLabel**: (task_id, label_id) PK
- **Comment**: id, task_id, author_id, body, created_at

All FKs `ON DELETE CASCADE` where the child cannot outlive the parent.

### Roles (hierarchy: owner > admin > member > viewer)

| Action | min role |
|---|---|
| read workspace, boards, tasks, comments | viewer |
| create/update/move/delete tasks, comment | member |
| create/update/delete boards, columns, labels; create/revoke invites; change roles of members below own role; remove members below own role | admin |
| rename/delete workspace; promote to admin; transfer ownership | owner |

Implemented once: `require_role(workspace_id, user_id, min_role)` in the workspaces service.
Non-members get **404** (do not leak existence), insufficient role gets **403**.

## API (all under `/api`, JSON, Bearer JWT)

Errors: `{"detail": "<message>", "code": "<snake_case_code>"}` with proper status.

### Auth
- `POST /api/auth/register` `{email, password(min 8), full_name}` → 201 `{access_token, token_type:"bearer", user}`
- `POST /api/auth/login` `{email, password}` → `{access_token, token_type, user}`; 401 on bad creds
- `GET /api/users/me` → `User`
- `PATCH /api/users/me` `{full_name?, avatar_color?}` → `User`
- `POST /api/users/me/password` `{current_password, new_password}` → 204

`User` = `{id, email, full_name, avatar_color, created_at}`

### Workspaces & members
- `GET /api/workspaces` → `[{id, name, role, created_at}]` (role = current user's)
- `POST /api/workspaces` `{name}` → 201 workspace (caller = owner)
- `PATCH /api/workspaces/{id}` `{name}` (owner)
- `DELETE /api/workspaces/{id}` (owner) → 204
- `GET /api/workspaces/{id}/members` → `[{user: User, role, joined_at}]`
- `PATCH /api/workspaces/{id}/members/{user_id}` `{role}` → member
- `DELETE /api/workspaces/{id}/members/{user_id}` → 204 (a member may remove themself = leave; owner cannot leave)

### Invites
- `GET /api/workspaces/{id}/invites` (admin) → `[Invite]`
- `POST /api/workspaces/{id}/invites` `{role?, expires_in_days?}` (admin) → 201 `Invite`
- `DELETE /api/workspaces/{id}/invites/{invite_id}` (admin) → 204 (revoke)
- `GET /api/invites/{token}` (auth optional) → `{workspace_name, inviter_name, role, valid}`
- `POST /api/invites/{token}/accept` → `{workspace_id}`; idempotent if already a member

`Invite` = `{id, token, role, created_at, expires_at, revoked, created_by: User}`

### Boards & columns
- `GET /api/workspaces/{id}/boards` → `[{id, name, description, created_at, task_count}]`
- `POST /api/workspaces/{id}/boards` `{name, description?}` → 201; creates default columns "To do", "In progress", "Done"
- `GET /api/boards/{id}` → `{id, workspace_id, name, description, columns: [Column & {tasks: [Task]}]}` sorted by position — a single call loads the whole board
- `PATCH /api/boards/{id}` / `DELETE /api/boards/{id}`
- `POST /api/boards/{id}/columns` `{name, color?}` → appended at end
- `PATCH /api/columns/{id}` `{name?, color?}`
- `POST /api/columns/{id}/move` `{position}` → reorders siblings
- `DELETE /api/columns/{id}` → 204 (cascades tasks)

### Tasks
- `POST /api/columns/{id}/tasks` `{title, description?, priority?, due_date?, assignee_ids?, label_ids?}` → 201 Task (appended at end)
- `GET /api/tasks/{id}` → TaskDetail (Task + comments)
- `PATCH /api/tasks/{id}` any of `{title, description, priority, due_date, assignee_ids, label_ids}`
- `POST /api/tasks/{id}/move` `{column_id, position}` → Task; column must be in the same board; positions of both columns are renumbered contiguously 0..n-1
- `DELETE /api/tasks/{id}` → 204
- `GET /api/me/tasks?workspace_id=&due_from=&due_to=` → `[Task & {board_id, board_name, column_name}]` — tasks assigned to the current user (powers "My tasks" and "Calendar")
- `POST /api/tasks/{id}/comments` `{body}` → 201 Comment; `DELETE /api/comments/{id}` (author or admin)
- Labels: `GET/POST /api/workspaces/{id}/labels`, `PATCH/DELETE /api/labels/{id}`

`Task` = `{id, column_id, title, description, priority, due_date, position, created_at, updated_at, created_by: User, assignees: [User], labels: [Label]}`
`Comment` = `{id, body, created_at, author: User}`

## Frontend pages

| Route | Page |
|---|---|
| `/login`, `/register` | auth (centered card) |
| `/invite/:token` | invite preview + accept (redirect to login if anonymous, then back) |
| `/w/:workspaceId` | boards grid + "assigned to me" summary |
| `/w/:workspaceId/b/:boardId` | kanban board with dnd-kit (tasks across columns, column reorder), optimistic updates |
| `/w/:workspaceId/my-tasks` | table of my tasks grouped by due (overdue / today / upcoming / no date) |
| `/w/:workspaceId/calendar` | month grid with tasks by due_date |
| `/w/:workspaceId/settings` | tabs: Profile, Workspace, Members (roles, invites) |

Task details open in a shadcn `Sheet` (right side) — not a giant modal.

### Design language (Apple-like on shadcn/ui)
- Font: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif`; tight headings (`tracking-tight`), body 14–15px.
- Neutral palette close to macOS: light bg `#F5F5F7`, surfaces white, dark bg `#000`/`#1C1C1E`, accent system blue `#007AFF` (`--primary`), system grays for borders/muted text. Defined as shadcn CSS variables; light + dark + system theme toggle.
- Radius: `--radius: 0.875rem`; cards `rounded-2xl`, inputs/buttons `rounded-xl`.
- Sidebar and top bar: translucent (`bg-background/70 backdrop-blur-xl`), hairline borders (`border-black/5`, `dark:border-white/10`).
- Soft shadows only on raised elements (cards while dragging, popovers); no heavy borders.
- Motion: 150–200ms ease-out; respect `prefers-reduced-motion`.
- Priority/column colors: Apple system colors (red `#FF3B30`, orange `#FF9500`, yellow `#FFCC00`, green `#34C759`, blue `#007AFF`, purple `#AF52DE`, gray `#8E8E93`).
- Empty states with an icon, one line of copy and a primary action. Loading = skeletons, not spinners.

## Definition of done
- `cd backend && uv run ruff check && uv run ruff format --check && uv run pytest` — all green; tests cover auth, role enforcement (404 vs 403), task move renumbering, invites accept/revoke/expired.
- `cd frontend && npm run build && npm run lint` — green, no TS errors.
- `docker compose up --build` serves the app on http://localhost:8080; register → create board → add/move task works.
- No secrets committed; `.env.example` documents every variable.

## Implementation notes (backend, as built)
- 422 validation errors: `{"detail": "<field: message; ...>", "code": "validation_error"}`.
- `POST /api/workspaces/{id}/boards` returns the full `BoardDetail` (with default columns).
- `GET /api/workspaces/{id}/invites` omits revoked invites.
- An invite's role must be strictly below the creator's role (admins invite member/viewer only) → otherwise 403 `insufficient_role`.
- Accepting a revoked/expired invite → 409 `invite_revoked` / `invite_expired`.
- Users cannot change their own role. Setting `owner` on a member transfers ownership; previous owner becomes `admin`.
- Removing a member drops their task assignments in that workspace.
- Moving a task to a missing column or a column on another board → 422 `column_not_in_board`.
- Health check: `GET /api/health` → `{"status":"ok"}`.
