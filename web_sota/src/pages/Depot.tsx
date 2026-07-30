import { useEffect, useState } from "react";
import { apiGet, apiPost, OutputEntry } from "../lib/api";
import { HardDrive, Play, FileText, ExternalLink, Search } from "lucide-react";

export default function Depot() {
  const [outputs, setOutputs] = useState<OutputEntry[]>([]);
  const [search, setSearch] = useState("");
  const [launching, setLaunching] = useState<string | null>(null);

  useEffect(() => {
    apiGet<{ outputs: OutputEntry[] }>("/api/outputs?limit=50")
      .then((d) => setOutputs(d.outputs))
      .catch(() => {});
  }, []);

  const filtered = search
    ? outputs.filter(
        (o) =>
          (o.project_name || "").toLowerCase().includes(search.toLowerCase()) ||
          o.name.toLowerCase().includes(search.toLowerCase()) ||
          (o.stack || "").toLowerCase().includes(search.toLowerCase())
      )
    : outputs;

  async function launchOutput(name: string) {
    setLaunching(name);
    try {
      await apiPost("/api/outputs/launch", { output_dir: name });
    } catch {
      // ignore
    }
    setLaunching(null);
  }

  function openDir(path: string) {
    fetch(`http://127.0.0.1:10738/api/outputs?limit=1`).catch(() => {});
    // The backend doesn't have a open-dir endpoint — just launch
  }

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
            <HardDrive size={18} /> App Depot
          </h1>
          <p className="text-sm text-zinc-400 mt-0.5">{outputs.length} built app(s)</p>
        </div>
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search outputs..."
            className="bg-zinc-800 border border-zinc-700 rounded text-sm pl-7 pr-2.5 py-1.5 text-zinc-200 w-52 placeholder-zinc-600 focus:outline-none focus:border-amber-500/50"
            data-testid="search-outputs"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-8 text-center">
          <HardDrive size={24} className="mx-auto mb-2 text-zinc-700" />
          <div className="text-sm text-zinc-400 mb-1">
            {outputs.length === 0 ? "No built apps yet" : "No outputs match your search"}
          </div>
          <div className="text-sm text-zinc-500">
            {outputs.length === 0
              ? "Use Chat or the factory pipeline to generate an app."
              : "Try a different search term."}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filtered.map((o) => (
            <div
              key={o.name}
              className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-zinc-200 truncate">
                      {o.project_name || o.name}
                    </h3>
                    {o.stack && (
                      <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded">
                        {o.stack}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-zinc-500">
                    <span>{o.name}</span>
                    {o.file_count != null && <span>{o.file_count} files</span>}
                    <span>{o.mtime_human}</span>
                  </div>
                  {o.readme_snippet && (
                    <p className="text-sm text-zinc-400 mt-2 line-clamp-2">
                      {o.readme_snippet}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 ml-4 flex-shrink-0">
                  <button
                    onClick={() => launchOutput(o.name)}
                    disabled={launching === o.name}
                    className="flex items-center gap-1 text-sm px-2.5 py-1.5 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 disabled:opacity-40 transition-colors"
                    title="Launch app"
                  >
                    {launching === o.name ? (
                      <span className="animate-pulse">...</span>
                    ) : (
                      <Play size={12} />
                    )}
                    Launch
                  </button>
                  <a
                    href={`http://127.0.0.1:10738/api/assess/${encodeURIComponent(o.name)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-sm px-2.5 py-1.5 rounded bg-zinc-800 text-zinc-300 hover:text-zinc-200 transition-colors"
                    title="View assessment"
                  >
                    <FileText size={12} />
                    Assess
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
