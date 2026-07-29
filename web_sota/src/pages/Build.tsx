import { useState, useEffect, useRef } from "react";
import { apiGet, apiPost, RunSummary, LLMModel } from "../lib/api";
import { useLLMStore } from "../store/llm";
import { Send, Square, Clock, ExternalLink } from "lucide-react";

export default function Build() {
  const [vibe, setVibe] = useState("");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<RunSummary | null>(null);
  const [logTail, setLogTail] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const providers = useLLMStore((s) => s.providers);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const selectedModel = useLLMStore((s) => s.selectedModel);

  const activeProvider = providers.find((p) => p.name === selectedProvider);
  const providerOk = activeProvider?.detected;

  useEffect(() => {
    apiGet<{ runs: RunSummary[] }>("/api/runs")
      .then((d) => setRuns(d.runs))
      .catch(() => {});
  }, []);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  async function startBuild() {
    if (!vibe.trim() || loading) return;
    setLoading(true);
    try {
      const body: Record<string, unknown> = { vibe_content: vibe.trim() };
      if (selectedModel) body.worker_model = selectedModel;
      await apiPost("/api/build", body);
      setVibe("");
      await new Promise((r) => setTimeout(r, 1000));
      const data = await apiGet<{ runs: RunSummary[] }>("/api/runs");
      setRuns(data.runs);
    } catch (e) {
      console.error("Build failed:", e);
    }
    setLoading(false);
  }

  function selectRun(run: RunSummary) {
    setSelectedRun(run);
    if (pollRef.current) clearInterval(pollRef.current);
    if (run.status === "running") {
      setPolling(true);
      pollRef.current = setInterval(async () => {
        try {
          const data = await apiGet<RunSummary & { log_tail?: string[] }>(`/api/run/${run.run_id}?log_tail=30`);
          setSelectedRun(data);
          if (data.log_tail) setLogTail(data.log_tail);
          if (data.status !== "running") {
            if (pollRef.current) clearInterval(pollRef.current);
            setPolling(false);
            const refreshed = await apiGet<{ runs: RunSummary[] }>("/api/runs");
            setRuns(refreshed.runs);
          }
        } catch { /* ignore */ }
      }, 3000);
    } else {
      fetchLog(run.run_id);
    }
  }

  async function fetchLog(runId: string) {
    try {
      const data = await apiGet<RunSummary & { log_tail?: string[] }>(`/api/run/${runId}?log_tail=50`);
      if (data.log_tail) setLogTail(data.log_tail);
    } catch { /* ignore */ }
  }

  async function stopRun(runId: string) {
    try {
      await apiPost(`/api/run/${runId}/stop`);
    } catch { /* ignore */ }
  }

  const running = runs.filter((r) => r.status === "running");

  return (
    <div className="p-6 max-w-5xl h-full flex flex-col">
      <h1 className="text-lg font-bold text-zinc-100 mb-4">Build</h1>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-4">
        <label className="text-xs text-zinc-500 block mb-1.5">Vibe description</label>
        <textarea
          value={vibe}
          onChange={(e) => setVibe(e.target.value)}
          placeholder="Describe the app to build. E.g.: Build a task management app with React and FastAPI, with user auth, CRUD for tasks, and a dashboard."
          rows={4}
          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500/50 resize-none"
          data-testid="build-input"
        />
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-2 text-xs text-zinc-600">
            {providerOk ? (
              <span className="text-green-500">LLM: {selectedModel || "auto"}</span>
            ) : (
              <span className="text-amber-500">No LLM detected</span>
            )}
            {running.length > 0 && (
              <span className="text-amber-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                {running.length} active
              </span>
            )}
          </div>
          <button
            onClick={startBuild}
            disabled={loading || !vibe.trim() || !providerOk}
            className="flex items-center gap-1.5 text-sm px-4 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 transition-colors"
            data-testid="build-start"
          >
            {loading ? <span className="animate-pulse">Starting...</span> : <><Send size={14} /> Build</>}
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 min-h-0">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 overflow-y-auto">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Runs ({runs.length})
          </h2>
          {runs.length === 0 ? (
            <p className="text-xs text-zinc-600">No builds yet. Describe your app above.</p>
          ) : (
            <div className="space-y-2">
              {runs.map((r) => (
                <button
                  key={r.run_id}
                  onClick={() => selectRun(r)}
                  className={`w-full text-left p-2 rounded text-xs transition-colors ${
                    selectedRun?.run_id === r.run_id
                      ? "bg-zinc-700 border border-zinc-600"
                      : "bg-zinc-800/50 border border-transparent hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`px-1 py-0.5 rounded text-[10px] font-medium ${
                      r.status === "running" ? "bg-amber-500/10 text-amber-400" :
                      r.status === "completed" ? "bg-green-500/10 text-green-400" :
                      r.status === "stopped" ? "bg-zinc-700 text-zinc-400" :
                      "bg-red-500/10 text-red-400"
                    }`}>{r.status}</span>
                    <span className="text-zinc-600">{new Date(r.started_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-zinc-400 truncate">{r.vibe_snippet || r.run_id}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 overflow-y-auto">
          {selectedRun ? (
            <>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                  {selectedRun.run_id}
                </h2>
                <div className="flex items-center gap-2">
                  {selectedRun.status === "running" && (
                    <button
                      onClick={() => stopRun(selectedRun.run_id)}
                      className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20"
                    >
                      <Square size={10} /> Stop
                    </button>
                  )}
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                    selectedRun.status === "running" ? "bg-amber-500/10 text-amber-400" :
                    selectedRun.status === "completed" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                  }`}>{selectedRun.status}</span>
                </div>
              </div>
              <div className="space-y-1 text-xs mb-3">
                <div className="flex justify-between text-zinc-500"><span>ID</span><span className="text-zinc-400 font-mono">{selectedRun.run_id}</span></div>
                {selectedRun.exit_code != null && <div className="flex justify-between text-zinc-500"><span>Exit</span><span className="text-zinc-400">{selectedRun.exit_code}</span></div>}
                {selectedRun.output_dir && <div className="flex justify-between text-zinc-500"><span>Output</span><span className="text-zinc-400">{selectedRun.output_dir}</span></div>}
              </div>
              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Log</h3>
              <div className="bg-black rounded p-2 max-h-[40vh] overflow-y-auto">
                {logTail.length === 0 ? (
                  <span className="text-zinc-700 text-[11px] font-mono">Waiting for output...</span>
                ) : (
                  logTail.map((line, i) => (
                    <div key={i} className="text-[11px] font-mono text-zinc-500 leading-5">{line}</div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-xs text-zinc-600">
              Select a run to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
