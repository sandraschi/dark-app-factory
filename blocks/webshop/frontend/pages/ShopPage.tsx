import { useState, useEffect } from "react";
import { ShoppingCart, Plus, Minus, Trash2 } from "lucide-react";

function getSessionId(): string {
  let sid = localStorage.getItem("shop_session_id");
  if (!sid) { sid = "sess_" + Math.random().toString(36).slice(2); localStorage.setItem("shop_session_id", sid); }
  return sid;
}

export function ShopPage({ apiBase }: { apiBase: string }) {
  const [products, setProducts] = useState<any[]>([]);
  const [cart, setCart] = useState<any[]>([]);
  const [category, setCategory] = useState("");
  const sessionId = getSessionId();

  useEffect(() => {
    fetch(`${apiBase}/api/products${category ? `?category=${category}` : ""}`).then((r) => r.json()).then((d) => setProducts(d.products || [])).catch(() => {});
    fetch(`${apiBase}/api/cart?session_id=${sessionId}`).then((r) => r.json()).then((d) => setCart(d.items || [])).catch(() => {});
  }, [category]);

  async function add(productId: number) {
    await fetch(`${apiBase}/api/cart/add`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sessionId, product_id: productId }) });
    const r = await fetch(`${apiBase}/api/cart?session_id=${sessionId}`).then((r2) => r2.json());
    setCart(r.items || []);
  }

  async function remove(productId: number) {
    await fetch(`${apiBase}/api/cart/remove`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sessionId, product_id: productId }) });
    const r = await fetch(`${apiBase}/api/cart?session_id=${sessionId}`).then((r2) => r2.json());
    setCart(r.items || []);
  }

  const cartTotal = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  const categories = [...new Set(products.map((p) => p.category).filter(Boolean))];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-zinc-100">Shop</h1>
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <ShoppingCart size={16} />
          <span>{cart.length} items (${cartTotal.toFixed(2)})</span>
        </div>
      </div>

      {categories.length > 0 && (
        <div className="flex gap-2 mb-4">
          <button onClick={() => setCategory("")} className={`text-xs px-2.5 py-1 rounded ${!category ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>All</button>
          {categories.map((c) => (
            <button key={c} onClick={() => setCategory(c)} className={`text-xs px-2.5 py-1 rounded ${category === c ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>{c}</button>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {products.map((p) => (
          <div key={p.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            {p.image_url && <img src={p.image_url} alt={p.name} className="w-full h-40 object-cover rounded mb-3" />}
            <h3 className="text-sm font-semibold text-zinc-200">{p.name}</h3>
            <p className="text-xs text-zinc-500 mt-1">{p.description}</p>
            <div className="flex items-center justify-between mt-3">
              <span className="text-lg font-bold text-zinc-100">${p.price.toFixed(2)}</span>
              <span className="text-[10px] text-zinc-600">{p.stock} in stock</span>
            </div>
            <button onClick={() => add(p.id)} disabled={p.stock < 1} className="mt-2 w-full py-1.5 bg-amber-500/10 text-amber-400 rounded-lg text-sm hover:bg-amber-500/20 disabled:opacity-30">
              {p.stock < 1 ? "Out of stock" : "Add to cart"}
            </button>
          </div>
        ))}
      </div>

      {cart.length > 0 && (
        <div className="mt-8 bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-zinc-200 mb-3">Cart ({cart.length})</h2>
          {cart.map((item, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0 text-sm">
              <span className="text-zinc-300">{item.name} x{item.quantity}</span>
              <div className="flex items-center gap-3">
                <span className="text-zinc-400">${(item.price * item.quantity).toFixed(2)}</span>
                <button onClick={() => remove(item.product_id)} className="text-zinc-600 hover:text-red-400"><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-zinc-800">
            <span className="text-sm font-bold text-zinc-100">Total: ${cartTotal.toFixed(2)}</span>
            <button onClick={() => window.location.href = "/checkout"} className="px-4 py-1.5 bg-amber-500 text-black rounded-lg text-sm font-medium hover:bg-amber-400">
              Checkout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
