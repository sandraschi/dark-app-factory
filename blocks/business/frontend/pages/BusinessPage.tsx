import { useState, useEffect } from "react";
import { Phone, Mail, MapPin, Clock, ChevronDown, CheckCircle } from "lucide-react";

export function ServiceCard({ service }: { service: any }) {
  return (
    <div className={`bg-zinc-900 border rounded-lg p-5 ${service.featured ? "border-amber-500/30 ring-1 ring-amber-500/20" : "border-zinc-800"}`}>
      {service.featured && <div className="text-[10px] text-amber-400 uppercase tracking-wider mb-2">Popular</div>}
      <h3 className="text-base font-semibold text-zinc-100">{service.name}</h3>
      <p className="text-sm text-zinc-400 mt-2">{service.description}</p>
      {(service.price || service.duration) && (
        <div className="flex items-center gap-3 mt-3 text-xs text-zinc-500">
          {service.price && <span className="text-lg font-bold text-amber-400">{service.price}</span>}
          {service.duration && <span>{service.duration}</span>}
        </div>
      )}
    </div>
  );
}

export function ContactForm({ apiBase }: { apiBase: string }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", message: "" });
  const [sent, setSent] = useState(false);
  async function submit() {
    await fetch(`${apiBase}/api/business/contact`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    setSent(true);
    setForm({ name: "", email: "", phone: "", message: "" });
  }
  if (sent) return <div className="bg-green-500/10 text-green-400 rounded-lg p-4 text-sm text-center">Thanks! We'll get back to you.</div>;
  return (
    <div className="space-y-3 max-w-md">
      <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Your name" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200" />
      <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="Email" type="email" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200" />
      <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone" className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200" />
      <textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="How can we help?" rows={4} className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 resize-none" />
      <button onClick={submit} disabled={!form.name || !form.message} className="w-full py-2.5 bg-amber-500 text-black rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50">Send Message</button>
    </div>
  );
}

export function FaqAccordion({ items }: { items: { question: string; answer: string }[] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="space-y-2 max-w-2xl">
      {items.map((item, i) => (
        <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
          <button onClick={() => setOpen(open === i ? null : i)} className="w-full flex items-center justify-between px-4 py-3 text-sm text-zinc-200 hover:bg-zinc-800 transition-colors">
            {item.question}
            <ChevronDown size={14} className={`text-zinc-500 transition-transform ${open === i ? "rotate-180" : ""}`} />
          </button>
          {open === i && <div className="px-4 pb-3 text-sm text-zinc-400">{item.answer}</div>}
        </div>
      ))}
    </div>
  );
}

export function BusinessPage({ apiBase }: { apiBase: string }) {
  const [info, setInfo] = useState<any>({});
  const [services, setServices] = useState<any[]>([]);
  const [team, setTeam] = useState<any[]>([]);
  const [faq, setFaq] = useState<any[]>([]);
  const [page, setPage] = useState("home");

  useEffect(() => {
    fetch(`${apiBase}/api/business/info`).then((r) => r.json()).then((d) => setInfo(d.info || {})).catch(() => {});
    fetch(`${apiBase}/api/business/services`).then((r) => r.json()).then((d) => setServices(d.services || [])).catch(() => {});
    fetch(`${apiBase}/api/business/team`).then((r) => r.json()).then((d) => setTeam(d.team || [])).catch(() => {});
    fetch(`${apiBase}/api/business/faq`).then((r) => r.json()).then((d) => setFaq(d.faq || [])).catch(() => {});
  }, []);

  const nav = [
    { id: "home", label: "Home" },
    { id: "services", label: "Services" },
    { id: "team", label: "Our Team" },
    { id: "faq", label: "FAQ" },
    { id: "contact", label: "Contact" },
  ];

  return (
    <div className="min-h-screen bg-zinc-950">
      <header className="border-b border-zinc-800 sticky top-0 bg-zinc-950/90 backdrop-blur z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-bold text-zinc-100">{info.name || "Our Business"}</h1>
          <nav className="flex gap-4">{nav.map((n) => (
            <button key={n.id} onClick={() => setPage(n.id)} className={`text-xs ${page === n.id ? "text-amber-400" : "text-zinc-500 hover:text-zinc-300"}`}>{n.label}</button>
          ))}</nav>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-12">
        {page === "home" && (
          <div>
            <div className="text-center py-16">
              <h2 className="text-4xl font-bold text-zinc-100 mb-4">{info.tagline || `Welcome to ${info.name}`}</h2>
              <p className="text-zinc-400 max-w-xl mx-auto mb-8">{info.about || `Professional ${info.name} services. Quality you can trust.`}</p>
              <button onClick={() => setPage("contact")} className="px-6 py-3 bg-amber-500 text-black rounded-lg font-medium hover:bg-amber-400">Get a Quote</button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { icon: MapPin, label: "Location", value: info.address || "Serving your area" },
                { icon: Phone, label: "Call Us", value: info.phone || "(555) 123-4567" },
                { icon: Mail, label: "Email", value: info.email || "info@example.com" },
                { icon: Clock, label: "Hours", value: info.hours || "Mon-Fri 9-5" },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 text-center">
                  <Icon size={20} className="mx-auto text-amber-500 mb-2" />
                  <div className="text-xs text-zinc-500">{label}</div>
                  <div className="text-sm text-zinc-200 font-medium mt-0.5">{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {page === "services" && (
          <div>
            <h2 className="text-2xl font-bold text-zinc-100 mb-8">Our Services</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {services.map((s) => <ServiceCard key={s.id} service={s} />)}
            </div>
          </div>
        )}

        {page === "team" && team.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-zinc-100 mb-8">Meet Our Team</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {team.map((m) => (
                <div key={m.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 text-center">
                  <div className="w-16 h-16 rounded-full bg-amber-500/20 mx-auto mb-3 flex items-center justify-center text-xl font-bold text-amber-500">
                    {m.name.charAt(0)}
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-200">{m.name}</h3>
                  <p className="text-xs text-amber-400">{m.role}</p>
                  {m.bio && <p className="text-xs text-zinc-500 mt-2">{m.bio}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {page === "faq" && (
          <div>
            <h2 className="text-2xl font-bold text-zinc-100 mb-8">Frequently Asked Questions</h2>
            <FaqAccordion items={faq.length > 0 ? faq : [
              { question: "What areas do you serve?", answer: "We serve the greater metropolitan area." },
              { question: "Do you offer emergency service?", answer: "Yes, call our emergency line for urgent needs." },
              { question: "How do I get a quote?", answer: "Contact us via phone or the form on this page." },
            ]} />
          </div>
        )}

        {page === "contact" && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-zinc-100 mb-4">Contact Us</h2>
            <div className="grid grid-cols-2 gap-4 mb-8 text-sm">
              {info.phone && <div className="flex items-center gap-2 text-zinc-400"><Phone size={14} /> {info.phone}</div>}
              {info.email && <div className="flex items-center gap-2 text-zinc-400"><Mail size={14} /> {info.email}</div>}
              {info.address && <div className="flex items-center gap-2 text-zinc-400 col-span-2"><MapPin size={14} /> {info.address}</div>}
            </div>
            <ContactForm apiBase={apiBase} />
          </div>
        )}
      </main>

      <footer className="border-t border-zinc-800 py-6 text-center text-xs text-zinc-600">
        &copy; {new Date().getFullYear()} {info.name}. All rights reserved.
      </footer>
    </div>
  );
}
