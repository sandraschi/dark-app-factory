import { useState, useEffect, useRef } from "react";
import { Send, Trash2, Download, Volume2 } from "lucide-react";
import { useLLMStore } from "../store/llm";
import { apiGet } from "../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  ts: string;
}

const HISTORY_KEY = "dark-app-factory-chat-history";
const PERSONALITY_KEY = "dark-app-factory-chat-personality";
const MAX_MESSAGES = 100;

const PERSONALITIES: Record<string, string> = {
  "research-assistant": "You are a helpful research assistant. Answer clearly and cite sources.",
  "expert-reviewer": "You are an expert code reviewer. Be thorough but constructive.",
  "quick-summarizer": "You are a summarizer. Keep responses brief and to the point.",
  "custom": "",
};

const EXAMPLE_PROMPTS = [
  "Build a task management app with React and FastAPI",
  "Create a blog CMS with admin panel",
  "Generate a landing page for a SaaS product",
  "Make a real-time chat app with WebSocket",
  "Build an e-commerce store with Stripe",
  "Create a dashboard for IoT device monitoring",
];

function stripMarkdown(md: string): string {
  return md.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[*_`#~]/g, "").replace(/```[\s\S]*?```/g, " ").replace(/\n+/g, " ").trim();
}

function SpeakButton({ text }: { text: string }) {
  const [speaking, setSpeaking] = useState(false);
  if (typeof window === "undefined" || !window.speechSynthesis) return null;
  return (
    <button
      onClick={() => {
        if (speaking) { window.speechSynthesis.cancel(); setSpeaking(false); return; }
        const plain = stripMarkdown(text);
        if (!plain) return;
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(plain);
        u.rate = 1; u.pitch = 1;
        u.onend = () => setSpeaking(false);
        window.speechSynthesis.speak(u);
        setSpeaking(true);
      }}
      className="p-1 rounded text-zinc-400 hover:text-zinc-300 transition-colors"
      title="Speak"
    >
      <Volume2 size={12} />
    </button>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try { const saved = localStorage.getItem(HISTORY_KEY); return saved ? JSON.parse(saved) : []; }
    catch { return []; }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [personalityId, setPersonalityId] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "research-assistant");
  const [customPrompt, setCustomPrompt] = useState("");
  const [skillContent, setSkillContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const selectedProvider = useLLMStore((s) => s.selectedProvider);
  const selectedModel = useLLMStore((s) => s.selectedModel);
  const providers = useLLMStore((s) => s.providers);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_MESSAGES)));
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personalityId);
  }, [personalityId]);

  useEffect(() => {
    apiGet<{ success: boolean; specialists: Array<{ name: string; docs: string }> }>("/api/specialists").then((d) => {
      if (d.success && d.specialists.length > 0) {
        const names = d.specialists.map((s) => s.name).join(", ");
        setSkillContent(`Dark App Factory has ${d.specialists.length} specialists: ${names}. Use them to generate full-stack apps.`);
      }
    }).catch((e) => console.error("Failed to load specialists:", e));
  }, []);

  const provider = providers.find((p) => p.name === selectedProvider);
  const baseUrl = provider?.base || (providers.find((p) => p.detected)?.base || "http://localhost:11434");
  const model = selectedModel || (providers.flatMap((p) => p.detected ? p.models : [])[0] || "");

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input.trim(), ts: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const personalityPrompt = PERSONALITIES[personalityId] || "";
      const systemPrompt = personalityId === "custom"
        ? customPrompt || skillContent || "You are Dark App Factory AI."
        : `${skillContent || "You are Dark App Factory AI."}\n\n---\n\n## Role\n${personalityPrompt}`;

      const history = messages.slice(-20).map((m) => ({ role: m.role, content: m.content }));
      const r = await fetch(`${baseUrl}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          messages: [
            { role: "system", content: systemPrompt },
            ...history,
            { role: "user", content: input.trim() },
          ],
          stream: false,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const reply = data.choices?.[0]?.message?.content || "No response.";
      const assistantMsg: Message = { role: "assistant", content: reply, ts: new Date().toISOString() };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      const errMsg: Message = { role: "assistant", content: `Error: ${e instanceof Error ? e.message : "Connection failed"}`, ts: new Date().toISOString() };
      setMessages((prev) => [...prev, errMsg]);
    }
    setLoading(false);
  }

  function clearChat() {
    setMessages([]);
    localStorage.removeItem(HISTORY_KEY);
  }

  function exportChat() {
    const text = messages.map((m) => `[${m.ts}] ${m.role}: ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `dark-app-factory-chat-${Date.now()}.txt`; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col h-full" data-testid="chat-page">
      <div className="flex items-center gap-2 p-3 border-b border-zinc-800" data-testid="chat-controls">
        <select
          value={personalityId}
          onChange={(e) => setPersonalityId(e.target.value)}
          className="bg-zinc-800 text-zinc-200 text-sm rounded px-2 py-1 border border-zinc-700"
          data-testid="personality-select"
        >
          <option value="research-assistant">Research Assistant</option>
          <option value="expert-reviewer">Expert Reviewer</option>
          <option value="quick-summarizer">Quick Summarizer</option>
          <option value="custom">Custom</option>
        </select>

        <div className="text-xs text-zinc-400 ml-auto">
          {provider?.detected ? `${model}` : "No LLM"}
        </div>

        <button onClick={exportChat} disabled={messages.length === 0} className="p-1.5 rounded text-zinc-300 hover:text-zinc-200 disabled:opacity-30" data-testid="chat-export" title="Export">
          <Download size={14} />
        </button>
        <button onClick={clearChat} disabled={messages.length === 0} className="p-1.5 rounded text-zinc-300 hover:text-zinc-200 disabled:opacity-30" data-testid="chat-clear" title="Clear">
          <Trash2 size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3" data-testid="chat-messages">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-zinc-400 text-sm mb-2">Start a conversation</div>
            <div className="text-zinc-500 text-xs">Describe the app you want to build</div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            <div className={`max-w-[80%] rounded-lg px-3 py-2 ${m.role === "user" ? "bg-amber-500/10 text-zinc-200" : "bg-zinc-800 text-zinc-300"}`}>
              <div className="text-xs whitespace-pre-wrap">{m.content}</div>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-[10px] text-zinc-500">{new Date(m.ts).toLocaleTimeString()}</span>
                {m.role === "assistant" && <SpeakButton text={m.content} />}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="bg-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-400">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-zinc-800 p-3">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3" data-testid="example-prompts">
            {EXAMPLE_PROMPTS.map((p) => (
              <button
                key={p}
                onClick={() => setInput(p)}
                className="text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded transition-colors"
              >
                {p}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())}
            placeholder={provider?.detected ? "Describe the app to build..." : "No LLM detected"}
            disabled={loading || !provider?.detected}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500/50 disabled:opacity-50"
            data-testid="chat-input"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim() || !provider?.detected}
            className="px-3 py-2 bg-amber-500/10 text-amber-400 rounded-lg hover:bg-amber-500/20 disabled:opacity-30 transition-colors"
            data-testid="chat-send"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
