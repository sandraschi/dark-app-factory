import { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";

interface PricingPlan {
  name: string;
  price: string;
  priceId: string;
  interval: string;
  features: string[];
  featured?: boolean;
}

const DEFAULT_PLANS: PricingPlan[] = [
  { name: "Starter", price: "$9", priceId: "price_starter", interval: "/month", features: ["3 projects", "Basic support", "1GB storage"] },
  { name: "Pro", price: "$29", priceId: "price_pro", interval: "/month", features: ["Unlimited projects", "Priority support", "50GB storage", "API access"], featured: true },
  { name: "Enterprise", price: "$99", priceId: "price_enterprise", interval: "/month", features: ["Everything in Pro", "Dedicated support", "Unlimited storage", "Custom integrations"] },
];

export function PricingPage({ apiBase, plans }: { apiBase: string; plans?: PricingPlan[] }) {
  const [loading, setLoading] = useState<string | null>(null);
  const activePlans = plans || DEFAULT_PLANS;

  async function checkout(priceId: string) {
    setLoading(priceId);
    try {
      const r = await fetch(`${apiBase}/api/stripe/create-checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ price_id: priceId, success_url: window.location.origin + "/success", cancel_url: window.location.origin + "/pricing" }),
      });
      const data = await r.json();
      if (data.url) window.location.href = data.url;
    } catch (e) { console.error("Checkout failed:", e); }
    setLoading(null);
  }

  return (
    <div className="py-12 px-4">
      <h1 className="text-2xl font-bold text-center text-zinc-100 mb-2">Pricing</h1>
      <p className="text-sm text-zinc-500 text-center mb-8">Choose the plan that fits your needs</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        {activePlans.map((plan) => (
          <div key={plan.name} className={`rounded-xl p-6 border ${plan.featured ? "bg-amber-500/5 border-amber-500/30" : "bg-zinc-900 border-zinc-800"}`}>
            {plan.featured && <div className="text-[10px] text-amber-400 uppercase tracking-wider mb-2">Most Popular</div>}
            <h3 className="text-lg font-semibold text-zinc-100">{plan.name}</h3>
            <div className="mt-2 mb-4">
              <span className="text-3xl font-bold text-zinc-100">{plan.price}</span>
              <span className="text-sm text-zinc-500">{plan.interval}</span>
            </div>
            <ul className="space-y-2 mb-6">
              {plan.features.map((f) => (
                <li key={f} className="text-sm text-zinc-400 flex items-center gap-2">
                  <span className="text-green-500">&#10003;</span> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => checkout(plan.priceId)}
              disabled={loading === plan.priceId}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${plan.featured ? "bg-amber-500 text-black hover:bg-amber-400" : "bg-zinc-800 text-zinc-200 hover:bg-zinc-700"} disabled:opacity-50`}
            >
              {loading === plan.priceId ? "Redirecting..." : "Subscribe"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export function CheckoutButton({ apiBase, priceId, children }: { apiBase: string; priceId: string; children: React.ReactNode }) {
  const [loading, setLoading] = useState(false);
  return (
    <button
      onClick={async () => {
        setLoading(true);
        const r = await fetch(`${apiBase}/api/stripe/create-checkout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ price_id: priceId }) });
        const d = await r.json();
        if (d.url) window.location.href = d.url;
        setLoading(false);
      }}
      disabled={loading}
      className="px-4 py-2 bg-amber-500 text-black rounded-lg text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
    >
      {loading ? "..." : children}
    </button>
  );
}
