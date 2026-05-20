# Skill: Task & Project Management App (2026 SOTA)

## 1. Domain Context
A collaborative task tracker / project management tool. Think Trello/Linear/Notion hybrid.
Single or multi-workspace, board + list + calendar views, assignments, comments, due dates.

## 2. Mandatory Pages & Routes
- `/` — Workspace overview: project cards with progress rings, recent activity
- `/projects/:id` — Project detail: tab strip (Board | List | Calendar | Files)
- `/projects/:id/board` — Kanban: draggable cards between status columns
- `/projects/:id/list` — Sortable table: title, assignee, priority, due date, status
- `/projects/:id/calendar` — Monthly view with tasks on their due dates
- `/tasks/:id` — Task detail modal/page: description (Markdown), subtasks, comments, attachments, activity log
- `/inbox` — Notifications: @mentions, due-soon alerts, assignment changes
- `/settings` — Workspace name, members, roles, integrations

## 3. Data Model (PostgreSQL preferred)
```sql
workspaces (id, name, slug, owner_id FK, created_at)
projects (id, workspace_id FK, name, description, colour, archived BOOL, created_at)
columns (id, project_id FK, name, position INT, colour)  -- Kanban columns
tasks (id, project_id FK, column_id FK, title, description_md TEXT,
       assignee_id FK, reporter_id FK, priority ENUM('none','low','medium','high','urgent'),
       due_date DATE, estimated_hours DECIMAL, position INT,
       status ENUM('open','in_progress','blocked','done'), created_at, updated_at)
subtasks (id, task_id FK, title, completed BOOL, position INT)
comments (id, task_id FK, author_id FK, body_md TEXT, created_at, updated_at)
attachments (id, task_id FK, filename, url, size_bytes, uploaded_by FK, created_at)
activity_logs (id, task_id FK, user_id FK, action, old_value, new_value, created_at)
```

## 4. Backend Specifics
- Drag-and-drop reorder: `PATCH /api/tasks/:id/reorder` accepts `{ column_id, position }`; use fractional indexing or batch reposition
- Real-time: WebSocket or SSE channel per project (`/api/projects/:id/events`); push `task.updated`, `comment.created` events
- @mention notifications: parse comment body for `@username` patterns, create notification records, push via SSE
- Due-date reminders: background job, daily at 08:00 local time, emails tasks due today/tomorrow
- Activity logging: every task mutation appends to `activity_logs` — non-negotiable

## 5. Frontend Specifics
- Kanban board: `@dnd-kit/core` for drag-and-drop (lighter than react-beautiful-dnd); smooth spring animation on drop
- Priority badges: coloured pills (`none`=grey, `low`=blue, `medium`=yellow, `high`=orange, `urgent`=red)
- Task card: show avatar, priority badge, due date chip, subtask completion fraction (e.g. `2/5`)
- Comment body: Markdown rendered with `react-markdown`; @mention highlighted in accent colour
- Calendar view: custom monthly grid — each day cell lists task titles truncated at 2 lines
- Keyboard shortcuts: `n` → new task, `e` → edit focused task, `Escape` → close modal

## 6. Design Tokens
- Background: `#0a0a0f` deep navy-black
- Surface cards: `#12121a` with `border border-indigo-900/40`
- Column headers: subtle gradient per column colour
- Accent: `#6366f1` (indigo-500) for primary actions, selections
- Urgent priority: `#ef4444`, High: `#f97316`, Medium: `#eab308`, Low: `#3b82f6`

## 7. Key Third-Party Integrations (all via env vars)
- `EMAIL_API_URL` — due-date reminders, @mention notifications
- `STORAGE_API_URL` — attachment uploads
- `WEBHOOK_URL` — outbound webhooks for automation (e.g. trigger on task completion)
- `SLACK_WEBHOOK_URL` — optional Slack notifications on task status changes
