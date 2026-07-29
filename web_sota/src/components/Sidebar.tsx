import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  HelpCircle,
  Terminal,
  BookOpen,
  Wrench,
  Inbox,
  HardDrive,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { HealthDot } from "./HealthDot";
import { useBackendStore } from "../store/llm";
import { useUIStore } from "../store/ui";

const NAV_ITEMS = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/inbox", icon: Inbox, label: "Inbox" },
  { to: "/depot", icon: HardDrive, label: "Depot" },
  { to: "/tools", icon: Wrench, label: "Tools" },
  { to: "/skills", icon: BookOpen, label: "Skills" },
  { to: "/chat", icon: MessageSquare, label: "Chat" },
  { to: "/settings", icon: Settings, label: "Settings" },
  { to: "/help", icon: HelpCircle, label: "Help" },
  { to: "/logs", icon: Terminal, label: "Logs" },
];

export function Sidebar() {
  const connected = useBackendStore((s) => s.connected);
  const open = useUIStore((s) => s.sidebarOpen);
  const toggle = useUIStore((s) => s.toggleSidebar);

  return (
    <aside
      className={`h-screen bg-zinc-950 border-r border-zinc-800 flex flex-col transition-all duration-200 ${
        open ? "w-56" : "w-14"
      }`}
    >
      <div className="flex items-center gap-2 p-3 border-b border-zinc-800">
        <div className="w-7 h-7 rounded bg-amber-500 flex items-center justify-center text-xs font-bold text-black flex-shrink-0">
          D
        </div>
        {open && <span className="text-sm font-semibold text-zinc-100">Factory</span>}
        <button
          onClick={toggle}
          className="ml-auto p-1 rounded hover:bg-zinc-800 text-zinc-400"
        >
          {open ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-2.5 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-amber-500/10 text-amber-400"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
              }`
            }
          >
            <item.icon size={16} className="flex-shrink-0" />
            {open && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-zinc-800 flex items-center gap-2">
        <HealthDot connected={connected} />
        {open && (
          <span className="text-xs text-zinc-500">
            {connected === null ? "..." : connected ? "Connected" : "Offline"}
          </span>
        )}
      </div>
    </aside>
  );
}
