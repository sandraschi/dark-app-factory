import { useState, useEffect } from "react";
import { Calendar, User, Tag, Search } from "lucide-react";

function renderMarkdown(md: string): string {
  return md.replace(/### (.+)/g, "<h3 class='text-lg font-semibold text-zinc-200 mt-4 mb-2'>$1</h3>")
    .replace(/## (.+)/g, "<h2 class='text-xl font-bold text-zinc-100 mt-5 mb-2'>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong class='text-zinc-200'>$1</strong>")
    .replace(/`(.+?)`/g, "<code class='bg-zinc-800 text-amber-400 px-1 rounded text-xs'>$1</code>")
    .replace(/^- (.+)$/gm, "<li class='text-zinc-400 text-sm ml-4'>$1</li>")
    .replace(/\n\n/g, "</p><p class='text-sm text-zinc-400 leading-6 mb-3'>")
    .replace(/^(.+)$/gm, (m: string) => m.startsWith("<") ? m : `<p class='text-sm text-zinc-400 leading-6 mb-3'>${m}</p>`);
}

export function ArticleCard({ article }: { article: any }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 hover:border-zinc-700 transition-colors">
      <div className="flex items-center gap-3 text-[10px] text-zinc-600 mb-2">
        <span className="flex items-center gap-1"><Calendar size={10} />{new Date(article.created_at).toLocaleDateString()}</span>
        {article.author && <span className="flex items-center gap-1"><User size={10} />{article.author}</span>}
        {article.category && <span className="flex items-center gap-1"><Tag size={10} />{article.category}</span>}
      </div>
      <h3 className="text-base font-semibold text-zinc-200 mb-1">{article.title}</h3>
      <p className="text-xs text-zinc-500 line-clamp-2">{article.content_md?.slice(0, 200)}</p>
      {article.tags?.length > 0 && (
        <div className="flex gap-1 mt-2">{article.tags.map((t: string) => <span key={t} className="text-[10px] bg-zinc-800 text-zinc-500 px-1.5 py-0.5 rounded">{t}</span>)}</div>
      )}
    </div>
  );
}

export function BlogPage({ apiBase }: { apiBase: string }) {
  const [articles, setArticles] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<any | null>(null);
  const [mode, setMode] = useState<"list" | "write">("list");
  const [form, setForm] = useState({ title: "", content_md: "", category: "", author: "", tags: "" });

  useEffect(() => {
    fetch(`${apiBase}/api/blog/articles?published=true`).then((r) => r.json()).then((d) => setArticles(d.articles || [])).catch(() => {});
    fetch(`${apiBase}/api/blog/categories`).then((r) => r.json()).then((d) => setCategories(d.categories || [])).catch(() => {});
  }, []);

  async function publish() {
    await fetch(`${apiBase}/api/blog/articles`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, published: true }) });
    setForm({ title: "", content_md: "", category: "", author: "", tags: "" });
    const r = await fetch(`${apiBase}/api/blog/articles?published=true`).then((r2) => r2.json());
    setArticles(r.articles || []);
  }

  const filtered = filter ? articles.filter((a) => a.category === filter || !filter) : articles;
  if (selected) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <button onClick={() => setSelected(null)} className="text-xs text-amber-400 hover:underline mb-4 block">&larr; Back</button>
        <h1 className="text-2xl font-bold text-zinc-100 mb-2">{selected.title}</h1>
        <div className="flex items-center gap-3 text-xs text-zinc-600 mb-6">
          <span><Calendar size={12} /> {new Date(selected.created_at).toLocaleDateString()}</span>
          <span><User size={12} /> {selected.author}</span>
          {selected.category && <span className="bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded text-[10px]">{selected.category}</span>}
        </div>
        <div className="prose prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: renderMarkdown(selected.content_md) }} />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-zinc-100">Blog</h1>
        <button onClick={() => setMode(mode === "list" ? "write" : "list")}
          className="text-xs px-3 py-1.5 bg-amber-500/10 text-amber-400 rounded hover:bg-amber-500/20">{mode === "list" ? "Write" : "View"}</button>
      </div>

      {mode === "write" ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3 max-w-2xl">
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Article title" className="w-full bg-zinc-800 border border-zinc-700 rounded text-sm px-3 py-2 text-zinc-200" />
          <div className="grid grid-cols-3 gap-2">
            <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Category" list="cats" className="bg-zinc-800 border border-zinc-700 rounded text-xs px-2 py-1.5 text-zinc-200" />
            <datalist id="cats">{categories.map((c) => <option key={c} value={c} />)}</datalist>
            <input value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} placeholder="Author" className="bg-zinc-800 border border-zinc-700 rounded text-xs px-2 py-1.5 text-zinc-200" />
            <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="Tags (comma)" className="bg-zinc-800 border border-zinc-700 rounded text-xs px-2 py-1.5 text-zinc-200" />
          </div>
          <textarea value={form.content_md} onChange={(e) => setForm({ ...form, content_md: e.target.value })} placeholder="Write in Markdown..." rows={10}
            className="w-full bg-zinc-800 border border-zinc-700 rounded text-sm px-3 py-2 text-zinc-200 font-mono resize-y" />
          <button onClick={publish} disabled={!form.title || !form.content_md}
            className="px-4 py-1.5 bg-amber-500 text-black rounded text-sm font-medium hover:bg-amber-400 disabled:opacity-50">Publish</button>
        </div>
      ) : (
        <>
          {categories.length > 0 && (
            <div className="flex gap-2 mb-4 flex-wrap">
              <button onClick={() => setFilter("")} className={`text-xs px-2.5 py-1 rounded ${!filter ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>All</button>
              {categories.map((c) => <button key={c} onClick={() => setFilter(c)} className={`text-xs px-2.5 py-1 rounded ${filter === c ? "bg-amber-500/10 text-amber-400" : "bg-zinc-800 text-zinc-400"}`}>{c}</button>)}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filtered.length === 0 ? <p className="text-sm text-zinc-600 col-span-2">No articles yet.</p> :
              filtered.map((a) => <div key={a.id} onClick={() => setSelected(a)} className="cursor-pointer"><ArticleCard article={a} /></div>)}
          </div>
        </>
      )}
    </div>
  );
}
