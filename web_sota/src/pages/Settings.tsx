import { useLLMStore } from "../store/llm";
import { useBackendStore } from "../store/llm";
import { useState, useEffect } from "react";
import { apiGet, apiPut } from "../lib/api";

export default function Settings() {
  const providers = useLLMStore((s) => s.providers);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const selectedModel = useLLMStore((s) => s.selectedModel);
  const setSelectedProvider = useLLMStore((s) => s.setSelectedProvider);
  const setSelectedModel = useLLMStore((s) => s.setSelectedModel);
  const status = useLLMStore((s) => s.status);
  const health = useBackendStore((s) => s.health);

  const activeProvider = providers.find((p) => p.name === selectedProvider);
  const models = activeProvider?.models || providers.flatMap((p) => p.detected ? p.models : []);
  const detectedProviders = providers.filter((p) => p.detected);

  return (
    <div className="p-6 max-w-2xl" data-testid="settings-page">
      <h1 className="text-lg font-bold text-zinc-100 mb-6">Settings</h1>

      <section className="mb-8">
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">LLM Provider</h2>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-500">Status</span>
            <span className={`text-xs ${status === "ready" ? "text-green-400" : status === "probing" ? "text-amber-400" : "text-red-400"}`}>
              {status === "ready" ? "Detected" : status === "probing" ? "Probing..." : "Not detected"}
            </span>
          </div>
          <div className="space-y-2">
            {providers.map((p) => (
              <div key={p.name} className="flex items-center justify-between text-xs">
                <span className="text-zinc-400 capitalize">{p.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${p.detected ? "bg-green-500" : "bg-zinc-700"}`} />
                  <span className="text-zinc-500">{p.detected ? `:${p.port}` : "Not found"}</span>
                </div>
              </div>
            ))}
          </div>

          {detectedProviders.length > 0 ? (
            <>
              <div>
                <label className="text-xs text-zinc-500 block mb-1">Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full bg-zinc-800 text-zinc-200 text-xs rounded px-2 py-1.5 border border-zinc-700"
                  data-testid="llm-provider-select"
                >
                  {detectedProviders.map((p) => (
                    <option key={p.name} value={p.name}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-500 block mb-1">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-zinc-800 text-zinc-200 text-xs rounded px-2 py-1.5 border border-zinc-700"
                  data-testid="llm-model-select"
                >
                  {models.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </>
          ) : (
            <div className="text-xs text-amber-500">Install Ollama or LM Studio to enable AI features.</div>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-zinc-300 mb-3">Backend</h2>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-2">
          <div className="flex justify-between text-xs"><span className="text-zinc-500">Server</span><span className="text-zinc-300">{health?.server || "..."}</span></div>
          <div className="flex justify-between text-xs"><span className="text-zinc-500">Version</span><span className="text-zinc-300">{health?.version || "..."}</span></div>
        </div>
      </section>
    </div>
  );
}
