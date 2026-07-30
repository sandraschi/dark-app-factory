import { useState, useEffect, useRef } from "react";
import { apiGet, apiPost, RunSummary } from "../lib/api";
import { useLLMStore } from "../store/llm";
import { Send, Square, Loader2, CheckCircle, XCircle, File, Sparkles, RefreshCw, Settings2 } from "lucide-react";

interface ProgressEvent {
  type: string; percentage?: number; status?: string;
  step?: { name: string; detail: string; status: string };
  name?: string; detail?: string; path?: string;
  specialists?: Record<string, string>; files?: string[]; steps?: any[];
}

const EXAMPLE_PROMPTS = [
  "Build a task management app with React and FastAPI, with user auth, CRUD for tasks, and a dashboard.",
  "Create a blog CMS with admin panel, Markdown editor, and comments.",
  "Generate a landing page for a SaaS product with pricing tiers and testimonials.",
  "Make a real-time chat app with WebSocket, channels, and user profiles.",
  "Build an e-commerce store with Stripe payments, cart, and product catalog.",
  "Create a dashboard for IoT device monitoring with charts and alerts.",
];

export default function Build() {
  const [vibe, setVibe] = useState("");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRun, setSelectedRun] = useState<RunSummary | null>(null);
  const [logTail, setLogTail] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);
  const [refining, setRefining] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [steps, setSteps] = useState<Array<{ name: string; detail: string; status: string }>>([]);
  const [specialists, setSpecialists] = useState<Record<string, string>>({});
  const [files, setFiles] = useState<string[]>([]);
  const [activeBuildId, setActiveBuildId] = useState<string | null>(null);
  const [showOptions, setShowOptions] = useState(false);
  const [foremanModel, setForemanModel] = useState("");
  const [workerModel, setWorkerModel] = useState("");
  const [outputName, setOutputName] = useState("");
  const sseRef = useRef<EventSource | null>(null);
  const fileListRef = useRef<HTMLDivElement>(null);

  const providers = useLLMStore((s) => s.providers);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const setSelectedProvider = useLLMStore((s) => s.setSelectedProvider);
  const setSelectedModel = useLLMStore((s) => s.setSelectedModel);
  const selectedModel = useLLMStore((s) => s.selectedModel);
  const status = useLLMStore((s) => s.status);

  const activeProvider = providers.find((p) => p.name === selectedProvider);
  const detectedModels = providers.flatMap((p) => p.detected ? p.models : []);
  const detectedProviders = providers.filter((p) => p.detected);
  const providerOk = status === "ready";

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
        const ev: ProgressEvent = JSON.parse(e.data);
        setProgress(ev);
        if (ev.type === "step_start" && ev.step) {
          setSteps((prev) => [...prev, { name: ev.step!.name, detail: ev.step!.detail, status: "running" }]);
        } else if (ev.type === "step_done" && ev.name) {
          setSteps((prev) => prev.map((s) => s.name === ev.name ? { ...s, status: ev.status || "done" } : s));
        } else if (ev.type === "specialist" && ev.name) {
          setSpecialists((prev) => ({ ...prev, [ev.name!]: ev.status || "running" }));
        } else if (ev.type === "file" && ev.path) {
          setFiles((prev) => [...prev, ev.path!]);
          if (fileListRef.current) fileListRef.current.scrollTop = fileListRef.current.scrollHeight;
        } else if (ev.type === "state" && ev.steps) {
          setSteps(ev.steps); if (ev.specialists) setSpecialists(ev.specialists); if (ev.files) setFiles(ev.files);
        }
      } catch { /* ignore */ }
    };
    es.onerror = () => { es.close(); sseRef.current = null; };
  }

  useEffect(() => {
    if (activeBuildId) connectSSE();
    else if (sseRef.current) { sseRef.current.close(); sseRef.current = null; }
    return () => { if (sseRef.current) sseRef.current.close(); };
  }, [activeBuildId]);

  async function startBuild() {
    if (!vibe.trim() || loading) return;
    setLoading(true);
    setSteps([]); setSpecialists({}); setFiles([]); setLogTail([]);
    try {
      const body: Record<string, unknown> = { vibe_content: vibe.trim() };
      if (selectedModel) body.worker_model = selectedModel;
      if (outputName) body.output_name = outputName;
      await apiPost("/api/build", body);
      setVibe("");
      await new Promise((r) => setTimeout(r, 1500));
      const data = await apiGet<{ runs: RunSummary[] }>("/api/runs");
      setRuns(data.runs);
      if (data.runs.length > 0) { const latest = data.runs[0]; setActiveBuildId(latest.run_id); selectRun(latest); }
    } catch (e) { console.error("Build failed:", e); }
    setLoading(false);
  }

  async function refinePrompt() {
    if (!vibe.trim() || refining) return;
    setRefining(true);
    try {
      const data = await apiPost<{ improved: string }>("/api/refine", { prompt: vibe.trim(), history: [] });
      if (data.improved) setVibe(data.improved);
    } catch { /* ignore */ }
    setRefining(false);
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
            setPolling(false); setActiveBuildId(null);
            const refreshed = await apiGet<{ runs: RunSummary[] }>("/api/runs");
            setRuns(refreshed.runs);
          }
        } catch { /* ignore */ }
      }, 3000);
    } else { fetchLog(run.run_id); }
  }

  async function fetchLog(runId: string) {
    try {
      const data = await apiGet<RunSummary & { log_tail?: string[] }>(`/api/run/${runId}?log_tail=50`);
      if (data.log_tail) setLogTail(data.log_tail);
    } catch { /* ignore */ }
  }

  async function stopRun(runId: string) {
    try { await apiPost(`/api/run/${runId}/stop`); } catch { /* ignore */ }
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
        <div className="flex items-center justify-between mb-2">
          <label className="text-xs text-zinc-500">Vibe description</label>
          <div className="flex items-center gap-2">
            <button onClick={refinePrompt} disabled={!vibe.trim() || refining}
              className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-zinc-800 text-zinc-400 hover:text-zinc-200 disabled:opacity-30 transition-colors">
              <Sparkles size={12} /> {refining ? "..." : "Refine"}
            </button>
            <button onClick={() => setShowOptions(!showOptions)}
              className={`flex items-center gap-1 text-[11px] px-2 py-1 rounded transition-colors ${showOptions ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"}`}>
              <Settings2 size={12} /> Options
            </button>
          </div>
        </div>

        <textarea value={vibe} onChange={(e) => setVibe(e.target.value)}
          placeholder="Describe the app to build..."
          rows={3}
          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500/50 resize-none"
          data-testid="build-input" />

        <div className="flex flex-wrap gap-1.5 mt-2" data-testid="example-prompts">
          {EXAMPLE_PROMPTS.map((p) => (
            <button key={p} onClick={() => setVibe(p)}
              className="text-[10px] bg-zinc-800 hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 px-2 py-1 rounded transition-colors">
              {p.length > 50 ? p.slice(0, 50) + "..." : p}
            </button>
          ))}
        </div>

        {showOptions && (
          <div className="mt-3 pt-3 border-t border-zinc-800 grid grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] text-zinc-600 block mb-1">Foreman model</label>
              <select value={foremanModel} onChange={(e) => setForemanModel(e.target.value)}
                className="w-full bg-zinc-800 text-zinc-300 text-xs rounded px-2 py-1.5 border border-zinc-700">
                <option value="">Default</option>
                {detectedModels.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-zinc-600 block mb-1">Worker model</label>
              <select value={workerModel} onChange={(e) => setWorkerModel(e.target.value)}
                className="w-full bg-zinc-800 text-zinc-300 text-xs rounded px-2 py-1.5 border border-zinc-700">
                <option value="">Default</option>
                {detectedModels.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-zinc-600 block mb-1">Output name</label>
              <input value={outputName} onChange={(e) => setOutputName(e.target.value)}
                placeholder="auto"
                className="w-full bg-zinc-800 border border-zinc-700 rounded text-xs px-2 py-1.5 text-zinc-300 placeholder-zinc-600" />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-3 text-xs text-zinc-600">
            {providerOk ? (
              <span className="text-green-500 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                {detectedProviders.map((p) => p.name).join(", ")}
              </span>
            ) : status === "probing" ? (
              <span className="text-amber-500 flex items-center gap-1">
                <Loader2 size={12} className="animate-spin" /> Detecting...
              </span>
            ) : (
              <span className="text-red-500 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                No LLM detected
              </span>
            )}
            {running.length > 0 && (
              <span className="text-amber-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                {running.length} active
              </span>
            )}
          </div>
          <button onClick={startBuild}
            disabled={loading || !vibe.trim() || !providerOk}
            className="flex items-center gap-1.5 text-sm px-4 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 transition-colors"
            data-testid="build-start">
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
                <button key={r.run_id} onClick={() => selectRun(r)}
                  className={`w-full text-left p-2 rounded text-xs transition-colors ${selectedRun?.run_id === r.run_id ? "bg-zinc-700 border border-zinc-600" : "bg-zinc-800/50 border border-transparent hover:border-zinc-700"}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`px-1 py-0.5 rounded text-[10px] font-medium ${r.status === "running" ? "bg-amber-500/10 text-amber-400" : r.status === "completed" ? "bg-green-500/10 text-green-400" : r.status === "stopped" ? "bg-zinc-700 text-zinc-400" : "bg-red-500/10 text-red-400"}`}>{r.status}</span>
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
                <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">{selectedRun.run_id}</h2>
                {selectedRun.status === "running" && (
                  <button onClick={() => stopRun(selectedRun.run_id)}
                    className="text-xs px-2 py-1 rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 flex items-center gap-1">
                    <Square size={10} /> Stop
                  </button>
                )}
              </div>
              {progress && progress.percentage != null && (
                <div className="mb-3">
                  <div className="flex justify-between text-[10px] text-zinc-500 mb-1">
                    <span>{progress.status}</span>
                    <span>{progress.percentage}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full transition-all duration-300" style={{ width: `${progress.percentage}%` }} />
                  </div>
                </div>
              )}
              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1.5">Steps</h3>
              <div className="space-y-1 mb-3">
                {steps.length === 0 ? <div className="text-[11px] text-zinc-700">Waiting...</div> : steps.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px]">
                    {statusIcon(s.status)}
                    <span className={s.status === "running" ? "text-zinc-300" : s.status === "done" ? "text-zinc-400" : "text-zinc-600"}>{s.name}</span>
                  </div>
                ))}
              </div>
              <h3 className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1.5">Specialists</h3>
              <div className="grid grid-cols-2 gap-1 mb-3">
                {Object.keys(specialists).length === 0 && steps.length === 0 ? <div className="text-[11px] text-zinc-700 col-span-2">Waiting...</div> : Object.entries(specialists).map(([name, st]) => (
                  <div key={name} className="flex items-center gap-1.5 text-[11px]">
                    {statusIcon(st)}
                    <span className={`truncate ${st === "running" ? "text-amber-300" : "text-zinc-500"}`}>{name}</span>
                  </div>
                ))}
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between text-zinc-500"><span>Exit</span><span className="text-zinc-400">{selectedRun.exit_code ?? "running"}</span></div>
                {selectedRun.output_dir && <div className="flex justify-between text-zinc-500"><span>Output</span><span className="text-zinc-400 text-[10px] truncate max-w-[140px]">{selectedRun.output_dir}</span></div>}
              </div>
            </>
          ) : <div className="flex items-center justify-center h-full text-xs text-zinc-600">Select a run</div>}
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
              logTail.map((line, i) => <div key={i} className="text-[11px] font-mono text-zinc-500 leading-5">{line}</div>)
            ) : <span className="text-zinc-700 text-[11px] font-mono">No log output yet</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
