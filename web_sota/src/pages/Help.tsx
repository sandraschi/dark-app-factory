import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

interface HelpDoc {
  id: string;
  title: string;
}

export default function Help() {
  const [docs, setDocs] = useState<HelpDoc[]>([]);
  const [content, setContent] = useState("");
  const [selected, setSelected] = useState("");

  useEffect(() => {
    apiGet<{ success: boolean; docs: HelpDoc[] }>("/api/help").then((d) => {
      if (d.success) setDocs(d.docs);
    }).catch((e) => console.error("Failed to load help docs:", e));
  }, []);

  useEffect(() => {
    if (selected) {
      apiGet<{ success: boolean; content: string }>(`/api/help/${selected}`).then((d) => {
        if (d.success) setContent(d.content);
      }).catch(() => setContent("Error loading doc."));
    }
  }, [selected]);

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-lg font-bold text-zinc-100 mb-6">Help & Documentation</h1>
      <div className="flex gap-6">
        <div className="w-48 flex-shrink-0 space-y-1">
          {docs.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelected(d.id)}
              className={`block w-full text-left text-sm px-2.5 py-1.5 rounded transition-colors ${
                selected === d.id ? "bg-amber-500/10 text-amber-400" : "text-zinc-300 hover:text-zinc-200 hover:bg-zinc-800"
              }`}
            >
              {d.title}
            </button>
          ))}
        </div>
        <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          {content ? (
            <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-sans">{content}</pre>
          ) : (
            <p className="text-sm text-zinc-500">Select a document from the left.</p>
          )}
        </div>
      </div>
    </div>
  );
}
