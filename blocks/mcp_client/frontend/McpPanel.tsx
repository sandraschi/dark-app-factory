import { useState, useEffect } from "react";
import { Play, Server, Wrench } from "lucide-react";

interface McpTool {
  name: string;
  description?: string;
  server: string;
  inputSchema?: { properties?: Record<string, unknown> };
}

interface ToolResponse {
  content?: Array<{ type: string; text?: string }>;
  isError?: boolean;
}

export function McpPanel({ apiBase }: { apiBase: string }) {
  const [tools, setTools] = useState<McpTool[]>([]);
  const [servers, setServers] = useState<Record<string, boolean>>({});
  const [selectedTool, setSelectedTool] = useState<McpTool | null>(null);
  const [args, setArgs] = useState("{}");
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${apiBase}/api/mcp/tools`)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          setTools(d.tools);
          setServers(d.servers);
        }
      })
      .catch(() => {});
  }, [apiBase]);

  async function callTool() {
    if (!selectedTool) return;
    setLoading(true);
    setResult("");
    try {
      let parsed: Record<string, unknown> = {};
      try { parsed = JSON.parse(args); } catch { /* use empty */ }
      const r = await fetch(`${apiBase}/api/mcp/${selectedTool.server}/${selectedTool.name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      });
      const data = await r.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (e) {
      setResult(`Error: ${e}`);
    }
    setLoading(false);
  }

  const serverList = Object.keys(servers);
  const groupByServer = (s: string) => tools.filter((t) => t.server === s);
  const toolNames = selectedTool ? tools.filter((t) => t.server === selectedTool.server).map((t) => t.name) : [];

  return (
    <div className="space-y-4">
      {serverList.length === 0 ? (
        <div className="text-sm text-zinc-500">No MCP servers configured. Set MCP_SERVERS env var.</div>
      ) : (
        <>
          <div className="flex gap-4">
            {serverList.map((s) => (
              <div key={s} className="flex items-center gap-1.5 text-xs text-zinc-400">
                <Server size={12} />
                <span>{s}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${servers[s] ? "bg-green-500" : "bg-red-500"}`} />
              </div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-zinc-500 block mb-1">Server</label>
              <select
                value={selectedTool?.server || ""}
                onChange={(e) => {
                  const sv = e.target.value;
                  const firstTool = tools.find((t) => t.server === sv);
                  setSelectedTool(firstTool || null);
                }}
                className="w-full bg-zinc-800 text-zinc-200 text-sm rounded px-2 py-1.5 border border-zinc-700"
              >
                <option value="">Select server</option>
                {serverList.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs text-zinc-500 block mb-1">Tool</label>
              <select
                value={selectedTool?.name || ""}
                onChange={(e) => {
                  const t = tools.find((x) => x.name === e.target.value && x.server === selectedTool?.server);
                  setSelectedTool(t || null);
                }}
                className="w-full bg-zinc-800 text-zinc-200 text-sm rounded px-2 py-1.5 border border-zinc-700"
              >
                <option value="">Select tool</option>
                {(selectedTool ? groupByServer(selectedTool.server) : tools).map((t) => (
                  <option key={`${t.server}/${t.name}`} value={t.name}>{t.name}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={callTool}
                disabled={!selectedTool || loading}
                className="flex items-center gap-1.5 text-sm px-4 py-1.5 rounded bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30"
              >
                <Play size={14} /> {loading ? "..." : "Call"}
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs text-zinc-500 block mb-1">Arguments (JSON)</label>
            <textarea
              value={args}
              onChange={(e) => setArgs(e.target.value)}
              rows={3}
              className="w-full bg-zinc-800 border border-zinc-700 rounded text-sm px-2 py-1.5 text-zinc-200 font-mono"
            />
          </div>

          {result && (
            <div>
              <label className="text-xs text-zinc-500 block mb-1">Result</label>
              <pre className="bg-black rounded p-2 text-xs text-zinc-300 max-h-60 overflow-auto whitespace-pre-wrap">
                {result}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
