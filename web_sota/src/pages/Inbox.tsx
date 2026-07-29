import { InboxIcon } from "lucide-react";

export default function Inbox() {
  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-lg font-bold text-zinc-100 mb-2 flex items-center gap-2"><InboxIcon size={18} /> Inbox</h1>
      <p className="text-xs text-zinc-500 mb-4">Build notifications and factory events.</p>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
        <div className="text-zinc-600 text-sm mb-1">No notifications yet</div>
        <div className="text-zinc-700 text-xs">Build events will appear here when the factory runs.</div>
      </div>
    </div>
  );
}
