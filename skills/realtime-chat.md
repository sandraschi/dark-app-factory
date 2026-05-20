# Skill: Real-Time Chat & Messaging App (2026 SOTA)

## 1. Domain Context
A Slack/Discord-style workspace messaging app with channels, direct messages, threads, and reactions.
Can also apply to a simpler in-app support chat or customer live chat widget.

## 2. Mandatory Pages & Routes
- `/` → redirect to `/app`
- `/login` — Email + password (or magic link)
- `/app` — Main layout: sidebar (workspaces, channels, DMs) + message pane + thread panel
- `/app/channels/:channelId` — Channel message feed
- `/app/dm/:userId` — Direct message feed
- `/app/search` — Full-text search across messages

### Settings (modal/pages)
- `/app/settings/profile` — Avatar, display name, status
- `/app/settings/notifications` — Per-channel notification preferences
- `/admin/channels` — Create, archive, set topic, manage members
- `/admin/members` — Role assignment, deactivate user

## 3. Data Model (PostgreSQL + Redis)
```sql
workspaces (id, name, slug, created_at)
users (id, workspace_id FK, email, display_name, avatar_url, status VARCHAR(100), role ENUM('admin','member'), created_at)
channels (id, workspace_id FK, name, topic, is_private BOOL, created_by FK, archived BOOL, created_at)
channel_members (channel_id FK, user_id FK, last_read_at TIMESTAMPTZ, PRIMARY KEY(channel_id, user_id))
messages (id, channel_id FK, user_id FK, body_md TEXT, edited_at TIMESTAMPTZ,
          thread_parent_id FK REFERENCES messages(id), created_at)
reactions (message_id FK, user_id FK, emoji VARCHAR(20), created_at, PRIMARY KEY(message_id, user_id, emoji))
direct_messages (id, from_user_id FK, to_user_id FK, body_md TEXT, read_at TIMESTAMPTZ, created_at)
```
Redis: presence (online/away/offline per user_id), unread counts, typing indicators TTL 3s.

## 4. Backend Specifics
- WebSocket server: one persistent connection per client; rooms = channel IDs
- Events emitted server → client: `message.new`, `message.edited`, `message.deleted`, `reaction.added`, `user.typing`, `user.presence`
- Events received client → server: `message.send`, `typing.start`, `channel.mark_read`
- Typing indicator: client sends `typing.start` every 2s while typing; server broadcasts to channel; TTL expires after 3s
- Unread count: Redis counter per `(user_id, channel_id)`, reset on `channel.mark_read`
- Message pagination: cursor-based (`GET /api/channels/:id/messages?before=<message_id>&limit=50`)
- Full-text search: PostgreSQL `tsvector` on `messages.body_md`

## 5. Frontend Specifics
- Message list: virtual scrolling (react-virtual) for channels with thousands of messages
- Message input: `contentEditable` div with Markdown shortcuts (bold, italic, code); Enter to send, Shift+Enter for newline
- Emoji reactions: hover a message → emoji picker popover → optimistic UI update
- Thread panel: slides in from right when clicking a reply count badge
- Unread badge: red pill on channel name in sidebar, bold channel name
- Online presence: green dot next to avatar when user is active

## 6. Real-Time Stack
- **Node backend**: `ws` or `socket.io` WebSocket server
- **Python backend**: `fastapi-websocket-pubsub` or `broadcaster` with Redis pubsub backend
- Horizontal scaling: Redis pubsub as message broker so multiple server instances share events

## 7. Key Third-Party Integrations (all via env vars)
- `EMAIL_API_URL` — email notification when mentioned while offline
- `STORAGE_API_URL` — file/image uploads in messages
- `SLACK_WEBHOOK_URL` — optional bridge to real Slack workspace
