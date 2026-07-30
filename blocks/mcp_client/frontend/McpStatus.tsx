import { Server } from "lucide-react";

export function McpStatus({ servers }: { servers: Record<string, boolean> }) {
  const entries = Object.entries(servers);
  if (entries.length === 0) return null;
  return (
    <div className="flex items-center gap-3">
      {entries.map(([name, alive]) => (
        <div key={name} className="flex items-center gap-1 text-xs">
          <Server size={12} className={alive ? "text-green-500" : "text-red-500"} />
          <span className="text-zinc-500">{name}</span>
          <span className={`w-1.5 h-1.5 rounded-full ${alive ? "bg-green-500" : "bg-red-500"}`} />
        </div>
      ))}
    </div>
  );
}
