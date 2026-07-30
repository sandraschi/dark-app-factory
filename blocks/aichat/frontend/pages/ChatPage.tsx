import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Bot, User, Sparkles } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; ts: number; }

const HISTORY_KEY = "aichat-history";
const PERSONALITIES: Record<string, string> = {
  helpful: "You are a helpful AI assistant. Be concise and clear.",
  friendly: "You are a friendly companion. Be warm and conversational.",
  expert: "You are an expert consultant. Be thorough and cite specifics.",
  creative: "You are a creative partner. Be imaginative and suggestive.",
};

export function ChatPage({ apiBase }: { apiBase: string }) {
  const [messages, setMessages] = useState<Message[]>(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch { return []; }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [personality, setPersonality] = useState("helpful");
  const [model, setModel] = useState(localStorage.getItem("aichat-model") || "llama3.1:8b");
  const [baseUrl, setBaseUrl] = useState(localStorage.getItem("aichat-base") || "http://localhost:11434/v1");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-100)));
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => { localStorage.setItem("aichat-model", model); }, [model]);
  useEffect(() => { localStorage.setItem("aichat-base", baseUrl); }, [baseUrl]);

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input.trim(), ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const history = messages.slice(-30).map((m) => ({ role: m.role, content: m.content }));
      const system = PERSONALITIES[personality] || PERSONALITIES.helpful;
      const r = await fetch(`${baseUrl}/v1/chat/completions`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, messages: [{ role: "system", content: system }, ...history, { role: "user", content: input.trim() }], stream: false }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const reply = data.choices?.[0]?.message?.content || "No response.";
      setMessages((prev) => [...prev, { role: "assistant", content: reply, ts: Date.now() }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${e instanceof Error ? e.message : "Connection failed"}`, ts: Date.now() }]);
    }
    setLoading(false);
  }

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <div className="flex items-center gap-2 p-3 border-b border-zinc-800">
        <select value={personality} onChange={(e) => setPersonality(e.target.value)}
          className="bg-zinc-800 text-zinc-200 text-xs rounded px-2 py-1 border border-zinc-700">
          {Object.keys(PERSONALITIES).map((k) => <option key={k} value={k}>{k.charAt(0).toUpperCase() + k.slice(1)}</option>)}
        </select>
        <input value={model} onChange={(e) => setModel(e.target.value)} className="bg-zinc-800 text-zinc-300 text-xs rounded px-2 py-1 border border-zinc-700 w-36" title="Model" />
        <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} className="bg-zinc-800 text-zinc-300 text-[10px] rounded px-2 py-1 border border-zinc-700 flex-1" title="API Base" />
        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => { setMessages([]); localStorage.removeItem(HISTORY_KEY); }} disabled={messages.length === 0}
            className="p-1.5 rounded text-zinc-400 hover:text-zinc-200 disabled:opacity-30"><Trash2 size={14} /></button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <Sparkles size={32} className="mx-auto text-zinc-700 mb-3" />
            <p className="text-zinc-500 text-sm mb-1">AI Chat</p>
            <p className="text-zinc-600 text-xs">Configure your model and start a conversation</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            <div className={`max-w-[75%] rounded-lg px-3 py-2 ${m.role === "user" ? "bg-amber-500/10 text-zinc-200" : "bg-zinc-800 text-zinc-300"}`}>
              <p className="text-sm whitespace-pre-wrap">{m.content}</p>
            </div>
          </div>
        ))}
        {loading && <div className="bg-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-500 w-fit animate-pulse">Thinking...</div>}
        <div ref={endRef} />
      </div>

      <div className="border-t border-zinc-800 p-3">
        <div className="flex gap-2">
          <input value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
            placeholder={model ? "Ask anything..." : "Configure a model first"}
            disabled={loading || !model}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500/50 disabled:opacity-50"
          />
          <button onClick={send} disabled={loading || !input.trim() || !model}
            className="px-3 py-2 bg-amber-500/10 text-amber-400 rounded-lg hover:bg-amber-500/20 disabled:opacity-30"><Send size={16} /></button>
        </div>
      </div>
    </div>
  );
}
