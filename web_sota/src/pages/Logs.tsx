import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";
import { Search, Download } from "lucide-react";

export default function Logs() {
  const [lines, setLines] = useState<string[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiGet<{ success: boolean; lines: string[] }>(`/api/logs?lines=200`).then((d) => {
      if (d.success) setLines(d.lines);
    }).catch(() => {});
  }, []);

  const filtered = search ? lines.filter((l) => l.toLowerCase().includes(search.toLowerCase())) : lines;

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-bold text-zinc-100">Logs</h1>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-600" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter..."
              className="bg-zinc-800 border border-zinc-700 rounded text-sm pl-7 pr-2 py-1.5 text-zinc-200 w-48"
            />
          </div>
          <a
            href="http://127.0.0.1:10738/api/logs/download"
            target="_blank"
            rel="noreferrer"
            className="p-1.5 rounded text-zinc-300 hover:text-zinc-200 bg-zinc-800"
            title="Download"
          >
            <Download size={14} />
          </a>
        </div>
      </div>
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 max-h-[70vh] overflow-y-auto">
        {filtered.length === 0 ? (
          <p className="text-sm text-zinc-500">No log entries.</p>
        ) : (
          filtered.map((line, i) => (
            <div key={i} className="text-[11px] font-mono text-zinc-400 leading-5 hover:bg-zinc-800 px-1 rounded">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
