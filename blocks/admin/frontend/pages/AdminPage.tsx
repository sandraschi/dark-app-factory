import { useState } from "react";
import { BarChart3, Users, Activity, Settings, Search, Plus } from "lucide-react";

interface CrudField { key: string; label: string; type?: "text" | "number" | "email" | "select"; options?: string[]; }

export function CrudTable({ title, fields, data, onAdd, onDelete }: {
  title: string; fields: CrudField[]; data: Record<string, any>[]; onAdd?: (item: Record<string, any>) => void; onDelete?: (id: number) => void;
}) {
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Record<string, any>>({});
  const filtered = data.filter((row) => fields.some((f) => String(row[f.key] || "").toLowerCase().includes(search.toLowerCase())));

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-200">{title} ({data.length})</h3>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-zinc-600" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search..." className="bg-zinc-800 border border-zinc-700 rounded text-xs pl-6 pr-2 py-1 text-zinc-200 w-36" />
          </div>
          {onAdd && <button onClick={() => setShowForm(!showForm)} className="p-1 rounded text-zinc-400 hover:text-zinc-200"><Plus size={14} /></button>}
        </div>
      </div>

      {showForm && onAdd && (
        <div className="grid grid-cols-2 gap-2 mb-3 p-2 bg-zinc-800 rounded">
          {fields.filter((f) => f.key !== "id").map((f) => (
            f.type === "select" ? (
              <select key={f.key} value={form[f.key] || ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                className="bg-zinc-700 text-xs rounded px-2 py-1 text-zinc-200">
                <option value="">{f.label}</option>{(f.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : (
              <input key={f.key} value={form[f.key] || ""} onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
                placeholder={f.label} type={f.type || "text"}
                className="bg-zinc-700 text-xs rounded px-2 py-1 text-zinc-200 placeholder-zinc-500" />
            )
          ))}
          <button onClick={() => { onAdd(form); setShowForm(false); setForm({}); }}
            className="col-span-2 py-1 bg-amber-500/10 text-amber-400 rounded text-xs hover:bg-amber-500/20">Add</button>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="text-zinc-500 border-b border-zinc-800">
            {fields.map((f) => <th key={f.key} className="text-left py-2 px-2 font-medium">{f.label}</th>)}
            {onDelete && <th className="w-8" />}
          </tr></thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={row.id || i} className="border-b border-zinc-800/50 text-zinc-300 hover:bg-zinc-800/50">
                {fields.map((f) => <td key={f.key} className="py-2 px-2">{String(row[f.key] ?? "")}</td>)}
                {onDelete && <td className="py-2"><button onClick={() => onDelete(row.id)} className="text-red-500 hover:text-red-400 text-[10px]">Del</button></td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function StatCard({ label, value, icon }: { label: string; value: string | number; icon?: React.ReactNode }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
      <div className="flex items-center gap-2 text-zinc-500 text-xs mb-1">{icon}{label}</div>
      <div className="text-xl font-bold text-zinc-100">{value}</div>
    </div>
  );
}

export function AdminPage({ apiBase, sections }: { apiBase: string; sections: { title: string; fields: CrudField[]; data: Record<string, any>[]; onAdd?: any; onDelete?: any }[] }) {
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2"><Settings size={20} /> Admin</h1>
      <div className="grid grid-cols-3 gap-3 mb-6">
        <StatCard label="Total Users" value={sections.reduce((s, sec) => s + sec.data.length, 0)} icon={<Users size={14} />} />
        <StatCard label="Active" value={sections.reduce((s, sec) => s + sec.data.filter((r: any) => r.status === "active" || !r.status).length, 0)} icon={<Activity size={14} />} />
        <StatCard label="Sections" value={sections.length} icon={<BarChart3 size={14} />} />
      </div>
      <div className="space-y-4">{sections.map((s, i) => <CrudTable key={i} {...s} />)}</div>
    </div>
  );
}
