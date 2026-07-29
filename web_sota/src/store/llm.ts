import { create } from "zustand";

export interface LLMProvider {
  name: string;
  port: number;
  base: string;
  detected: boolean;
  models: string[];
}

interface LLMState {
  providers: LLMProvider[];
  selectedProvider: string;
  selectedModel: string;
  status: "probing" | "ready" | "none";
  setProviders: (providers: LLMProvider[]) => void;
  setSelectedProvider: (name: string) => void;
  setSelectedModel: (model: string) => void;
  setStatus: (status: "probing" | "ready" | "none") => void;
}

const savedProvider = localStorage.getItem("llm_provider") || "";
const savedModel = localStorage.getItem("llm_model") || "";

export const useLLMStore = create<LLMState>((set) => ({
  providers: [],
  selectedProvider: savedProvider,
  selectedModel: savedModel,
  status: "probing",
  setProviders: (providers) => set({ providers }),
  setSelectedProvider: (name) => {
    localStorage.setItem("llm_provider", name);
    set({ selectedProvider: name, selectedModel: "" });
  },
  setSelectedModel: (model) => {
    localStorage.setItem("llm_model", model);
    set({ selectedModel: model });
  },
  setStatus: (status) => set({ status }),
}));

interface HealthData {
  status: string;
  server?: string;
  version: string;
}

interface BackendState {
  health: HealthData | null;
  statusData: DashboardStatus | null;
  connected: boolean | null;
  setHealth: (h: HealthData | null) => void;
  setStatusData: (s: DashboardStatus | null) => void;
  setConnected: (c: boolean) => void;
}

export const useBackendStore = create<BackendState>((set) => ({
  health: null,
  statusData: null,
  connected: null,
  setHealth: (health) => set({ health }),
  setStatusData: (statusData) => set({ statusData }),
  setConnected: (connected) => set({ connected }),
}));

import type { DashboardStatus } from "../lib/api";
