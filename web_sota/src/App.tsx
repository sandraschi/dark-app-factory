import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Settings from "./pages/Settings";
import Help from "./pages/Help";
import Logs from "./pages/Logs";
import Skills from "./pages/Skills";
import Tools from "./pages/Tools";
import Inbox from "./pages/Inbox";
import Depot from "./pages/Depot";
import Build from "./pages/Build";
import { useBackendStore, useLLMStore } from "./store/llm";
import { useEffect } from "react";
import { apiGet } from "./lib/api";
import type { Health, DashboardStatus, LLMModel } from "./lib/api";

function BackendPoller() {
  const setHealth = useBackendStore((s) => s.setHealth);
  const setConnected = useBackendStore((s) => s.setConnected);
  const setStatusData = useBackendStore((s) => s.setStatusData);
  const setProviders = useLLMStore((s) => s.setProviders);
  const setStatus = useLLMStore((s) => s.setStatus);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const setSelectedModel = useLLMStore((s) => s.setSelectedModel);

  useEffect(() => {
    let delay = 1000;
    let mounted = true;
    const poll = async () => {
      try {
        const [h, st, models] = await Promise.all([
          apiGet<Health>("/api/v1/health"),
          apiGet<DashboardStatus>("/api/status").catch(() => null),
          apiGet<{ models: LLMModel[] }>("/api/models").catch(() => ({ models: [] })),
        ]);
        if (!mounted) return;
        setHealth(h);
        setConnected(true);
        setStatusData(st);
        delay = 10000;

        const modelMap = new Map<string, string[]>();
        for (const m of models.models) {
          const list = modelMap.get(m.provider) || [];
          list.push(m.id);
          modelMap.set(m.provider, list);
        }
        const providerList = [
          { name: "ollama", port: 11434, base: "http://localhost:11434", detected: modelMap.has("ollama"), models: modelMap.get("ollama") || [] },
          { name: "lmstudio", port: 1234, base: "http://localhost:1234", detected: modelMap.has("lmstudio"), models: modelMap.get("lmstudio") || [] },
        ];
        setProviders(providerList);
        const detected = providerList.filter((p) => p.detected);
        setStatus(detected.length > 0 ? "ready" : "none");

        const saved = localStorage.getItem("llm_provider");
        if (saved && detected.find((p) => p.name === saved)) {
          const savedModel = localStorage.getItem("llm_model");
          const prov = detected.find((p) => p.name === saved);
          if (savedModel && prov?.models.includes(savedModel)) {
            setSelectedModel(savedModel);
          }
        }
      } catch {
        if (!mounted) return;
        setHealth(null);
        setConnected(false);
        delay = Math.min(delay * 2, 16000);
      }
      if (mounted) setTimeout(poll, delay);
    };
    poll();
    return () => { mounted = false; };
  }, []);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <BackendPoller />
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="build" element={<Build />} />
          <Route path="inbox" element={<Inbox />} />
          <Route path="depot" element={<Depot />} />
          <Route path="tools" element={<Tools />} />
          <Route path="skills" element={<Skills />} />
          <Route path="chat" element={<Chat />} />
          <Route path="settings" element={<Settings />} />
          <Route path="help" element={<Help />} />
          <Route path="logs" element={<Logs />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
