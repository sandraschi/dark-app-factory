import { useState, useEffect } from "react";
import { Bell, Check, CheckCheck, Info, AlertTriangle, XCircle } from "lucide-react";

const PRIORITY_ICONS: Record<string, any> = { low: Info, normal: Bell, high: AlertTriangle, critical: XCircle };
const PRIORITY_COLORS: Record<string, string> = { low: "text-blue-400", normal: "text-amber-400", high: "text-red-400", critical: "text-red-600" };

export function NotificationsPage({ apiBase, userId = 1 }: { apiBase: string; userId?: number }) {
  const [notifs, setNotifs] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${apiBase}/api/notifications?user_id=${userId}`).then((r) => r.json()).then((d) => setNotifs(d.notifications || [])).catch(() => {});
  }, []);

  async function markRead(id: number) {
    await fetch(`${apiBase}/api/notifications/${id}/read`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: userId }) });
    setNotifs(notifs.map((n) => n.id === id ? { ...n, read: true } : n));
  }

  async function markAllRead() {
    await fetch(`${apiBase}/api/notifications/mark-all-read`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ user_id: userId }) });
    setNotifs(notifs.map((n) => ({ ...n, read: true })));
  }

  const unread = notifs.filter((n) => !n.read).length;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2"><Bell size={20} /> Notifications</h1>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-zinc-500">{unread} unread</span>
          {unread > 0 && <button onClick={markAllRead} className="text-amber-400 hover:underline flex items-center gap-1"><CheckCheck size={14} /> Mark all read</button>}
        </div>
      </div>

      {notifs.length === 0 ? (
        <div className="text-center py-12 text-sm text-zinc-600">No notifications yet.</div>
      ) : (
        <div className="space-y-2">
          {notifs.map((n) => {
            const Icon = PRIORITY_ICONS[n.priority] || Bell;
            const color = PRIORITY_COLORS[n.priority] || "text-zinc-400";
            return (
              <div key={n.id} className={`bg-zinc-900 border rounded-lg p-3 flex items-start gap-3 transition-colors ${n.read ? "border-zinc-800 opacity-60" : "border-zinc-700"}`}>
                <Icon size={16} className={`${color} mt-0.5 flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-zinc-200">{n.title}</span>
                    {!n.read && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />}
                  </div>
                  <p className="text-xs text-zinc-500">{n.message}</p>
                  <div className="flex items-center gap-2 mt-1 text-[10px] text-zinc-600">
                    <span>{n.channel}</span>
                    <span>{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                </div>
                {!n.read && (
                  <button onClick={() => markRead(n.id)} className="p-1 rounded text-zinc-600 hover:text-zinc-400 flex-shrink-0" title="Mark read">
                    <Check size={14} />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
