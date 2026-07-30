import { useState, useEffect } from "react";
import { BarChart3, TrendingUp, Globe, Activity } from "lucide-react";

export function AnalyticsPage({ apiBase }: { apiBase: string }) {
  const [data, setData] = useState<any>({});
  useEffect(() => { fetch(`${apiBase}/api/analytics/dashboard?hours=72`).then((r) => r.json()).then(setData).catch(() => {}); }, []);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-xl font-bold text-zinc-100 mb-6 flex items-center gap-2"><BarChart3 size={20} /> Analytics</h1>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><div className="text-xs text-zinc-500 flex items-center gap-1"><Activity size={12} />Pageviews</div><div className="text-xl font-bold text-zinc-100 mt-1">{data.total_pageviews || 0}</div></div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><div className="text-xs text-zinc-500 flex items-center gap-1"><TrendingUp size={12} />Visitors</div><div className="text-xl font-bold text-zinc-100 mt-1">{data.unique_sessions || 0}</div></div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><div className="text-xs text-zinc-500 flex items-center gap-1"><Globe size={12} />Referrers</div><div className="text-xl font-bold text-zinc-100 mt-1">{(data.top_referrers || []).length}</div></div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><div className="text-xs text-zinc-500 flex items-center gap-1"><Activity size={12} />Events</div><div className="text-xl font-bold text-zinc-100 mt-1">{data.total_events || 0}</div></div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><h3 className="text-sm font-semibold text-zinc-200 mb-3">Top Pages</h3>
          {(data.top_pages || []).map(([path, count]: [string, number]) => (
            <div key={path} className="flex justify-between text-xs text-zinc-400 py-1 border-b border-zinc-800 last:border-0"><span>{path}</span><span className="text-zinc-300 font-medium">{count}</span></div>
          ))}
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4"><h3 className="text-sm font-semibold text-zinc-200 mb-3">Top Referrers</h3>
          {(data.top_referrers || []).map(([ref, count]: [string, number]) => (
            <div key={ref} className="flex justify-between text-xs text-zinc-400 py-1 border-b border-zinc-800 last:border-0"><span>{ref}</span><span className="text-zinc-300 font-medium">{count}</span></div>
          ))}
        </div>
      </div>
      {data.recent_events?.length > 0 && (
        <div className="mt-4 bg-zinc-900 border border-zinc-800 rounded-lg p-4"><h3 className="text-sm font-semibold text-zinc-200 mb-3">Recent Events</h3>
          {data.recent_events.slice(0, 10).map((e: any, i: number) => (
            <div key={i} className="text-xs text-zinc-500 py-0.5"><span className="text-zinc-400">{e.name}</span> — {e.category}{e.label ? `: ${e.label}` : ""}</div>
          ))}
        </div>
      )}
    </div>
  );
}
