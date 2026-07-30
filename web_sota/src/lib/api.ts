const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:10738";
export { API_BASE };

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`GET ${path}: ${r.status}`);
  return r.json();
}

export async function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`POST ${path}: ${r.status}`);
  return r.json();
}

export async function apiPut<T = unknown>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`PUT ${path}: ${r.status}`);
  return r.json();
}

export interface Health {
  status: string;
  server?: string;
  version: string;
}

export interface DashboardStatus {
  active_builds: number;
  last_verdict: string;
  settings_provider: string;
}

export interface RunSummary {
  run_id: string;
  status: string;
  exit_code: number | null;
  started_at: string;
  output_dir: string;
  vibe_snippet: string;
}

export interface OutputEntry {
  name: string;
  path: string;
  mtime_human: string;
  stack: string;
  project_name: string;
  file_count: number | null;
  readme_snippet: string;
}

export interface LLMModel {
  id: string;
  provider: string;
}

export interface Specialist {
  name: string;
  owned_patterns: string[];
  requires: string[];
  temperature: number;
  docs: string;
}

export interface LogResponse {
  success: boolean;
  lines: string[];
  file: string;
}

export interface HelpDoc {
  id: string;
  title: string;
}
