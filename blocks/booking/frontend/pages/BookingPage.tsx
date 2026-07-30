import { useState, useEffect } from "react";
import { Calendar, Clock, ChevronLeft, ChevronRight } from "lucide-react";

export function CalendarPicker({ onSelect }: { onSelect: (date: string) => void }) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth());
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 max-w-xs">
      <div className="flex items-center justify-between mb-3">
        <button onClick={() => { if (month === 0) { setYear(year - 1); setMonth(11); } else setMonth(month - 1); }} className="text-zinc-400 hover:text-zinc-200"><ChevronLeft size={16} /></button>
        <span className="text-sm font-medium text-zinc-200">{new Date(year, month).toLocaleString("default", { month: "long", year: "numeric" })}</span>
        <button onClick={() => { if (month === 11) { setYear(year + 1); setMonth(0); } else setMonth(month + 1); }} className="text-zinc-400 hover:text-zinc-200"><ChevronRight size={16} /></button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-[10px] text-zinc-500 text-center mb-1">{days.map((d) => <div key={d}>{d}</div>)}</div>
      <div className="grid grid-cols-7 gap-1 text-center">
        {Array.from({ length: firstDay }, (_, i) => <div key={`e${i}`} />)}
        {Array.from({ length: lastDate }, (_, i) => {
          const d = i + 1;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
          return (
            <button key={d} onClick={() => onSelect(dateStr)}
              className="text-xs w-7 h-7 rounded hover:bg-amber-500/10 hover:text-amber-400 text-zinc-400 transition-colors">
              {d}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function BookingPage({ apiBase }: { apiBase: string }) {
  const [slots, setSlots] = useState<any[]>([]);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [view, setView] = useState<"book" | "list">("book");

  useEffect(() => {
    fetch(`${apiBase}/api/booking/slots`).then((r) => r.json()).then((d) => setSlots(d.slots || [])).catch(() => {});
    fetch(`${apiBase}/api/booking/appointments`).then((r) => r.json()).then((d) => setAppointments(d.appointments || [])).catch(() => {});
  }, []);

  async function book() {
    if (!selectedSlot || !name || !email) return;
    await fetch(`${apiBase}/api/booking/appointments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ start: selectedSlot, customer_name: name, customer_email: email }) });
    setSelectedSlot(null); setName(""); setEmail("");
    const r = await fetch(`${apiBase}/api/booking/appointments`).then((r2) => r2.json());
    setAppointments(r.appointments || []);
  }

  const grouped = slots.reduce((acc: Record<string, any[]>, s) => {
    const day = s.start.slice(0, 10);
    (acc[day] = acc[day] || []).push(s);
    return acc;
  }, {});

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <Calendar size={20} className="text-amber-500" />
        <h1 className="text-xl font-bold text-zinc-100">Bookings</h1>
        <div className="ml-auto flex gap-2">
          <button onClick={() => setView("book")} className={`text-xs px-2.5 py-1 rounded ${view === "book" ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>Book</button>
          <button onClick={() => setView("list")} className={`text-xs px-2.5 py-1 rounded ${view === "list" ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>Appointments ({appointments.length})</button>
        </div>
      </div>

      {view === "book" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4 max-h-[60vh] overflow-y-auto">
            {Object.entries(grouped).map(([day, daySlots]) => (
              <div key={day}>
                <h3 className="text-xs font-semibold text-zinc-400 mb-2">{new Date(day).toLocaleDateString("default", { weekday: "long", month: "short", day: "numeric" })}</h3>
                <div className="grid grid-cols-2 gap-1.5">
                  {daySlots.map((s) => (
                    <button key={s.id} onClick={() => setSelectedSlot(s.start)}
                      className={`text-xs px-2 py-1.5 rounded border text-left ${selectedSlot === s.start ? "bg-amber-500/10 border-amber-500/30 text-amber-400" : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-600"}`}>
                      {new Date(s.start).toLocaleTimeString("default", { hour: "2-digit", minute: "2-digit" })}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-zinc-200 mb-3">Confirm Booking</h3>
            {selectedSlot && <p className="text-xs text-zinc-500 mb-3">{new Date(selectedSlot).toLocaleString()}</p>}
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" className="w-full bg-zinc-800 border border-zinc-700 rounded text-sm px-3 py-2 text-zinc-200 mb-2" />
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full bg-zinc-800 border border-zinc-700 rounded text-sm px-3 py-2 text-zinc-200 mb-3" />
            <button onClick={book} disabled={!selectedSlot || !name || !email}
              className="w-full py-2 bg-amber-500 text-black rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50">Confirm</button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {appointments.length === 0 ? <p className="text-sm text-zinc-600">No appointments.</p> : appointments.map((a) => (
            <div key={a.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 flex items-center justify-between">
              <div>
                <div className="text-sm text-zinc-200">{a.customer_name}</div>
                <div className="text-xs text-zinc-500">{new Date(a.start).toLocaleString()} - {a.customer_email}</div>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${a.status === "confirmed" ? "bg-green-500/10 text-green-400" : "bg-zinc-700 text-zinc-500"}`}>{a.status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
