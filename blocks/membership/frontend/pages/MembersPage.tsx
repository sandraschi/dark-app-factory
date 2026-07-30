import { useState, useEffect } from "react";
import { Users, Search, Mail, Phone, Building2, Briefcase } from "lucide-react";

interface Person {
  id: number; name: string; email: string; phone?: string; status: string; role?: string;
  company?: string; department?: string; position?: string;
}

export function MembersPage({ apiBase, type = "members", title = "Members" }: { apiBase: string; type?: "members" | "customers" | "employees"; title?: string }) {
  const [people, setPeople] = useState<Person[]>([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", department: "", position: "" });

  useEffect(() => {
    fetch(`${apiBase}/api/${type}${type === "customers" && search ? `?search=${search}` : ""}`)
      .then((r) => r.json()).then((d) => setPeople(d[type] || [])).catch(() => {});
  }, [type, search]);

  async function addPerson() {
    const r = await fetch(`${apiBase}/api/${type === "members" ? "auth/register" : type}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, password: "changeme", role: type === "employees" ? "employee" : "customer" }),
    });
    if (r.ok) { setShowForm(false); setForm({ name: "", email: "", phone: "", company: "", department: "", position: "" }); window.location.reload(); }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2"><Users size={20} /> {title}</h1>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-600" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search..." className="bg-zinc-800 border border-zinc-700 rounded text-xs pl-7 pr-2.5 py-1.5 text-zinc-200 w-48" />
          </div>
          {type !== "members" && <button onClick={() => setShowForm(!showForm)} className="text-xs px-3 py-1.5 bg-amber-500/10 text-amber-400 rounded hover:bg-amber-500/20">Add {type === "customers" ? "Customer" : "Employee"}</button>}
        </div>
      </div>

      {showForm && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-4 grid grid-cols-2 gap-3">
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" />
          <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" />
          <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" />
          {type === "customers" && <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="Company" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" />}
          {type === "employees" && <><input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} placeholder="Department" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" />
            <input value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} placeholder="Position" className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200" /></>}
          <button onClick={addPerson} className="col-span-2 py-1.5 bg-amber-500/10 text-amber-400 rounded text-sm hover:bg-amber-500/20">Save</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {people.length === 0 ? (
          <p className="text-sm text-zinc-600 col-span-2">No {title.toLowerCase()} yet.</p>
        ) : people.map((p) => (
          <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-semibold text-zinc-200">{p.name}</h3>
                <div className="flex items-center gap-3 text-xs text-zinc-500 mt-1">
                  <span className="flex items-center gap-1"><Mail size={10} /> {p.email}</span>
                  {p.phone && <span className="flex items-center gap-1"><Phone size={10} /> {p.phone}</span>}
                </div>
                {p.company && <div className="text-xs text-zinc-600 mt-1 flex items-center gap-1"><Building2 size={10} /> {p.company}</div>}
                {p.department && <div className="text-xs text-zinc-600 mt-1 flex items-center gap-1"><Briefcase size={10} /> {p.department}{p.position ? ` - ${p.position}` : ""}</div>}
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${p.status === "active" ? "bg-green-500/10 text-green-400" : "bg-zinc-700 text-zinc-500"}`}>{p.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ProfileCard({ member }: { member: { name: string; email: string; role: string; phone?: string } }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 max-w-sm">
      <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center text-lg font-bold text-amber-500 mb-3">
        {member.name.charAt(0).toUpperCase()}
      </div>
      <h3 className="text-sm font-semibold text-zinc-200">{member.name}</h3>
      <p className="text-xs text-zinc-500">{member.email}</p>
      <div className="flex gap-2 mt-2">
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">{member.role}</span>
        {member.phone && <span className="text-[10px] text-zinc-600">{member.phone}</span>}
      </div>
    </div>
  );
}
