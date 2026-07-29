import { useEffect, useState } from "react";
import { Wrench } from "lucide-react";

const STATIC_TOOLS = [
  { name: "factory_fleet", description: "Dashboard health, log tailing, settings and launch" },
  { name: "factory_run", description: "Start a full factory generation run from a vibe" },
  { name: "factory_status", description: "Poll run status or list all runs" },
  { name: "factory_stop", description: "Cancel a running build" },
  { name: "factory_launch", description: "Launch the generated app" },
  { name: "factory_assess", description: "Analyse generated output with Prefab card" },
  { name: "factory_outputs", description: "List completed generation outputs" },
];

export default function Tools() {
  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-lg font-bold text-zinc-100 mb-2 flex items-center gap-2"><Wrench size={18} /> Tools</h1>
      <p className="text-xs text-zinc-500 mb-4">MCP tools exposed by the Dark App Factory server (port 10739).</p>
      <div className="space-y-2">
        {STATIC_TOOLS.map((t) => (
          <div key={t.name} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3">
            <div className="text-sm font-medium text-amber-400 font-mono">{t.name}</div>
            <div className="text-xs text-zinc-500 mt-0.5">{t.description}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
