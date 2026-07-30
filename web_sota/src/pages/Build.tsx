import { useState, useEffect, useRef } from "react";
import { apiGet, apiPost, RunSummary, LLMModel } from "../lib/api";
import { useLLMStore } from "../store/llm";
import { Send, Square, Clock, HardDrive, CheckCircle, XCircle, Loader2, File } from "lucide-react";

interface ProgressEvent {
  type: string;
  percentage?: number;
  status?: string;
  step?: { name: string; detail: string; status: string };
  name?: string;
  detail?: string;
  path?: string;
  run_id?: string;
  specialists?: Record<string, string>;
  files?: string[];
  steps?: Array<{ name: string; detail: string; status: string }>;
}

export default function Build() {
  const [vibe, setVibe] = useState("");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<RunSummary | null>(null);
  const [logTail, setLogTail] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [steps, setSteps] = useState<Array<{ name: string; detail: string; status: string }>>([]);
  const [specialists, setSpecialists] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<string[]>([]);
  const [activeBuildId, setActiveBuildId] = useState<string | null>(null);
  const sseRef = useRef<EventSource | null>(null);
  const providers = useLLMStore((s) => s.providers);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const selectedModel = useLLMStore((s) => s.selectedModel);
  const activeProvider = providers.find((p) => p.name === selectedProvider);
  const providerOk = activeProvider?.detected;
  const fileListRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiGet<{ runs: RunSummary[] }>("/api/runs")
      .then((d) => setRuns(d.runs))
      .catch(() => {});
  }, []);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); if (sseRef.current) sseRef.current.close(); };
  }, []);

  function connectSSE() {
    if (sseRef.current) sseRef.current.close();
    const es = new EventSource("http://127.0.0.1:10738/api/progress/stream");
    sseRef.current = es;
    es.onmessage = (e) => {
      try {
        const event: ProgressEvent = JSON.parse(e.data);
        setProgress(event);
        if (event.type === "step_start" && event.step) {
          setSteps((prev) => [...prev, { name: event.step!.name, detail: event.step!.detail, status: "running" }]);
        } else if (event.type === "step_done" && event.name) {
          setSteps((prev) => prev.map((s) => s.name === event.name ? { ...s, status: event.status || "done" } : s));
        } else if (event.type === "specialist" && event.name) {
          setSpecialists((prev) => ({ ...prev, [event.name!]: event.status || "running" }));
        } else if (event.type === "file" && event.path) {
          setFiles((prev) => [...prev, event.path!]);
          if (fileListRef.current) {
            fileListRef.current.scrollTop = fileListRef.current.scrollHeight;
          }
        } else if (event.type === "state" && event.steps) {
          setSteps(event.steps);
          if (event.specialists) setSpecialists(event.specialists);
          if (event.files) setFiles(event.files);
        }
      } catch { /* ignore parse errors */ }
    };
    es.onerror = () => {
      es.close();
      sseRef.current = null;
    };
  }

  useEffect(() => {
    if (activeBuildId) connectSSE();
    else if (sseRef.current) { sseRef.current.close(); sseRef.current = null; }
    return () => { if (sseRef.current) sseRef.current.close(); };
  }, [activeBuildId]);

  async function startBuild() {
    if (!vibe.trim() || loading) return;
    setLoading(true);
    setSteps([]);
    setSpecialists({});
    setFiles([]);
    setLogTail([]);
    try {
      const body: Record<string, unknown> = { vibe_content: vibe.trim() };
      if (selectedModel) body.worker_model = selectedModel;
      await apiPost("/api/build", body);
      setVibe("");
      await new Promise((r) => setTimeout(r, 1500));
      const data = await apiGet<{ runs: RunSummary[] }>("/api/runs");
      setRuns(data.runs);
      if (data.runs.length > 0) {
        const latest = data.runs[0];
        setActiveBuildId(latest.run_id);
        selectRun(latest);
      }
    } catch (e) {
      console.error("Build failed:", e);
    }
    setLoading(false);
  }

  function selectRun(run: RunSummary) {
    setSelectedRun(run);
    if (pollRef.current) clearInterval(pollRef.current);
    setActiveBuildId(run.status === "running" ? run.run_id : null);
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
            setActiveBuildId(null);
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

  function statusIcon(st: string) {
    if (st === "running") return <Loader2 size={12} className="animate-spin text-amber-400" />;
    if (st === "done" || st === "completed") return <CheckCircle size={12} className="text-green-500" />;
    if (st === "failed" || st === "error") return <XCircle size={12} className="text-red-500" />;
    return <span className="w-3 h-3 rounded-full bg-zinc-700 inline-block" />;
  }

  const running = runs.filter((r) => r.status === "running");

  return (
    <div className="p-6 max-w-6xl h-full flex flex-col">
      <h1 className="text-lg font-bold text-zinc-100 mb-4">Build</h1>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-4">
        <label className="text-xs text-zinc-500 block mb-1.5">Vibe description</label>
        <textarea
          value={vibe}
          onChange={(e) => setVibe(e.target.value)}
          placeholder="Describe the app to build. E.g.: Build a task management app with React and FastAPI, with user auth, CRUD for tasks, and a dashboard."
          rows={3}
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
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            {loading ? "Starting..." : "Build"}
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 overflow-y-auto">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Runs ({runs.length})
          </h2>
          {runs.length === 0 ? (
            <p className="text-xs text-zinc-600">No builds yet.</p>
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
                    <button onClick={() => stopRun(selectedRun.run_id)}
                      className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 flex items-center gap-1">
                      <Square size={10} /> Stop
                    </button>
                  )}
                </div>
              </div>

              {progress && progress.percentage != null && (
                <div className="mb-3">
                  <div className="flex justify-between text-[10px] text-zinc-500 mb-1">
                    <span>{progress.status}</span>
                    <span>{progress.percentage}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full transition-all duration-300"
                      style={{ width: `${progress.percentage}%` }} />
                  </div>
                </div>
              )}

              <div className="space-y-1 text-xs mb-3">
                <div className="flex justify-between text-zinc-500"><span>Exit</span><span className="text-zinc-400">{selectedRun.exit_code ?? "running"}</span></div>
                {selectedRun.output_dir && <div className="flex justify-between text-zinc-500"><span>Output</span><span className="text-zinc-400 text-[10px] truncate max-w-[140px]">{selectedRun.output_dir}</span></div>}
              </div>

              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1.5">Steps</h3>
              <div className="space-y-1 mb-3">
                {steps.length === 0 ? (
                  <div className="text-[11px] text-zinc-700">Waiting for build to start...</div>
                ) : (
                  steps.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-[11px]">
                      {statusIcon(s.status)}
                      <span className={`${s.status === "running" ? "text-zinc-300" : s.status === "done" ? "text-zinc-400" : "text-zinc-600"}`}>{s.name}</span>
                    </div>
                  ))
                )}
              </div>

              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1.5">Specialists</h3>
              <div className="grid grid-cols-2 gap-1 mb-3">
                {Object.keys(specialists).length === 0 && steps.length === 0 ? (
                  <div className="text-[11px] text-zinc-700 col-span-2">Waiting...</div>
                ) : (
                  Object.entries(specialists).map(([name, st]) => (
                    <div key={name} className="flex items-center gap-1.5 text-[11px]">
                      {statusIcon(st)}
                      <span className={`truncate ${st === "running" ? "text-amber-300" : "text-zinc-500"}`}>{name}</span>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-xs text-zinc-600">Select a run</div>
          )}
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 overflow-y-auto" ref={fileListRef}>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Log</h2>
            {files.length > 0 && <span className="text-[10px] text-zinc-600">{files.length} files</span>}
          </div>

          {files.length > 0 && (
            <div className="mb-3">
              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Generated files</h3>
              <div className="space-y-0.5 max-h-40 overflow-y-auto">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[10px] text-zinc-500">
                    <File size={10} />
                    <span className="truncate">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Console</h3>
          <div className="bg-black rounded p-2 max-h-[40vh] overflow-y-auto">
            {logTail.length === 0 && files.length === 0 ? (
              <span className="text-zinc-700 text-[11px] font-mono">Waiting...</span>
            ) : logTail.length > 0 ? (
              logTail.map((line, i) => (
                <div key={i} className="text-[11px] font-mono text-zinc-500 leading-5">{line}</div>
              ))
            ) : (
              <span className="text-zinc-700 text-[11px] font-mono">No log output yet</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
