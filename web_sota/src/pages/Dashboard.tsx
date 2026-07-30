import { useBackendStore } from "../store/llm";
import { HealthDot } from "../components/HealthDot";
import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";
import type { RunSummary, OutputEntry } from "../lib/api";
import { Play, Square, Clock, HardDrive } from "lucide-react";

export default function Dashboard() {
  const health = useBackendStore((s) => s.health);
  const statusData = useBackendStore((s) => s.statusData);
  const connected = useBackendStore((s) => s.connected);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [outputs, setOutputs] = useState<OutputEntry[]>([]);

  useEffect(() => {
    apiGet<{ runs: RunSummary[] }>("/api/runs").then((d) => setRuns(d.runs)).catch((e) => console.error("Failed to load runs:", e));
    apiGet<{ outputs: OutputEntry[] }>("/api/outputs?limit=5").then((d) => setOutputs(d.outputs)).catch((e) => console.error("Failed to load outputs:", e));
  }, []);

  return (
    <div className="p-6 max-w-5xl" data-testid="dashboard">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-lg font-bold text-black">D</div>
        <div>
          <h1 className="text-xl font-bold text-zinc-100">Dark App Factory</h1>
          <p className="text-sm text-zinc-400">Generate full-stack web apps from plain text</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4" data-testid="kpi-server">
          <div className="text-sm text-zinc-400 mb-1">Backend</div>
          <div className="flex items-center gap-2">
            <HealthDot connected={connected} />
            <span className="text-sm font-medium text-zinc-200">{connected === null ? "..." : connected ? "Connected" : "Offline"}</span>
          </div>
          {health && <div className="text-xs text-zinc-500 mt-1">v{health.version}</div>}
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4" data-testid="kpi-tools">
          <div className="text-sm text-zinc-400 mb-1">Status</div>
          <div className="text-sm font-medium text-zinc-200">{statusData?.last_verdict || "Idle"}</div>
          <div className="text-xs text-zinc-500 mt-1">{statusData?.active_builds || 0} active builds</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <div className="text-sm text-zinc-400 mb-1">Runs</div>
          <div className="text-lg font-bold text-zinc-100">{runs.length}</div>
          <div className="text-xs text-zinc-500 mt-1">{runs.filter((r) => r.status === "running").length} active</div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <div className="text-sm text-zinc-400 mb-1">Outputs</div>
          <div className="text-lg font-bold text-zinc-100">{outputs.length}</div>
          <div className="text-xs text-zinc-500 mt-1">generated apps</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-zinc-200 mb-3 flex items-center gap-2"><Clock size={14} /> Recent Runs</h2>
          {runs.length === 0 ? (
            <p className="text-sm text-zinc-500">No runs yet. Use Chat or start a build.</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {runs.slice(0, 10).map((r) => (
                <div key={r.run_id} className="flex items-center justify-between text-xs">
                  <span className="text-zinc-300 truncate max-w-[200px]">{r.vibe_snippet}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                    r.status === "running" ? "bg-amber-500/10 text-amber-400" :
                    r.status === "completed" ? "bg-green-500/10 text-green-400" :
                    "bg-red-500/10 text-red-400"
                  }`}>{r.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-zinc-200 mb-3 flex items-center gap-2"><HardDrive size={14} /> Recent Outputs</h2>
          {outputs.length === 0 ? (
            <p className="text-sm text-zinc-500">No outputs yet.</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {outputs.map((o) => (
                <div key={o.name} className="text-xs">
                  <div className="text-zinc-300 font-medium">{o.project_name || o.name}</div>
                  <div className="text-zinc-400">{o.stack} &middot; {o.mtime_human}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
