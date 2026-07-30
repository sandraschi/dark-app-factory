import { useState } from "react";
import { LogIn, UserPlus, Users } from "lucide-react";

export function LoginPage({ apiBase, onLogin }: { apiBase: string; onLogin?: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError("");
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body: Record<string, string> = { email, password };
      if (mode === "register") body.name = name;
      const r = await fetch(`${apiBase}${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const data = await r.json();
      if (!r.ok) { setError(data.detail || "Error"); return; }
      localStorage.setItem("token", data.token);
      localStorage.setItem("member", JSON.stringify(data.member));
      if (onLogin) onLogin(data.token);
      else window.location.href = "/";
    } catch (e) { setError("Connection failed"); }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4">
      <div className="w-full max-w-sm bg-zinc-900 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-6">
          {mode === "login" ? <LogIn size={20} className="text-amber-500" /> : <UserPlus size={20} className="text-amber-500" />}
          <h1 className="text-lg font-bold text-zinc-100">{mode === "login" ? "Sign In" : "Create Account"}</h1>
        </div>

        {error && <div className="text-sm text-red-400 bg-red-500/10 rounded px-3 py-2 mb-4">{error}</div>}

        {mode === "register" && (
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 mb-3" />
        )}
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="Email" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 mb-3" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 mb-4" />

        <button onClick={submit} disabled={loading} className="w-full py-2 bg-amber-500 text-black rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50">
          {loading ? "..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>

        <p className="text-sm text-zinc-500 text-center mt-4">
          {mode === "login" ? "No account? " : "Already have an account? "}
          <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }} className="text-amber-400 hover:underline">
            {mode === "login" ? "Register" : "Sign In"}
          </button>
        </p>
      </div>
    </div>
  );
}
