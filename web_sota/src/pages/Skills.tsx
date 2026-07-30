import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";
import { BookOpen } from "lucide-react";

interface Specialist {
  name: string;
  owned_patterns: string[];
  requires: string[];
  temperature: number;
  docs: string;
}

export default function Skills() {
  const [specialists, setSpecialists] = useState<Specialist[]>([]);

  useEffect(() => {
    apiGet<{ success: boolean; specialists: Specialist[] }>("/api/specialists").then((d) => {
      if (d.success) setSpecialists(d.specialists);
    }).catch((e) => console.error("Failed to load specialists:", e));
  }, []);

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-lg font-bold text-zinc-100 mb-2 flex items-center gap-2"><BookOpen size={18} /> Skills</h1>
      <p className="text-sm text-zinc-400 mb-4">Specialist council members available for code generation.</p>
      <div className="grid grid-cols-2 gap-3">
        {specialists.map((s) => (
          <div key={s.name} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-semibold text-zinc-200">{s.name}</h3>
              <span className="text-[10px] text-zinc-400">{s.temperature}</span>
            </div>
            <div className="text-sm text-zinc-400 mb-1">
              {s.owned_patterns?.join(", ") || "Generalist"}
            </div>
            {s.requires?.length > 0 && (
              <div className="text-[10px] text-zinc-500">Requires: {s.requires.join(", ")}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
