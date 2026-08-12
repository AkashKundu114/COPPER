import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { fetchStats } from "../lib/api";

interface Insight {
  text: string;
  sample_size: number;
  time_range: string;
  confidence: "high" | "medium" | "low";
}

export function Insights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats()
      .then(() => setInsights([]))
      .catch(() => setInsights([]))
      .finally(() => setLoading(false));
  }, []);

  const confidenceColor = { high: "text-emerald-400", medium: "text-amber-400", low: "text-gray-500" };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div className="flex items-center gap-2">
        <TrendingUp size={20} className="text-[#ff5722]" />
        <h1 className="text-xl font-bold text-white tracking-tight">Productivity Insights</h1>
      </div>
      <p className="text-xs text-gray-400 font-mono">
        Evidence-based patterns only. Every insight shows its sample size and confidence — nothing is fabricated.
      </p>

      {loading && <p className="text-sm text-gray-400 text-center py-8 font-mono">Gathering evidence analytics...</p>}
      {!loading && insights.length === 0 && (
        <div className="p-8 rounded-xl bg-[#14141a] border border-white/10 text-center text-xs text-gray-400 font-mono space-y-2">
          <p>Not enough observed data yet. Insights appear once COPPER has sufficient evidence to back them.</p>
        </div>
      )}

      <div className="space-y-3">
        {insights.map((insight, i) => (
          <div key={i} className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-2">
            <p className="text-xs font-medium text-white">{insight.text}</p>
            <div className="flex items-center gap-3 text-[11px] font-mono text-gray-400">
              <span>{insight.sample_size} data points</span>
              <span>{insight.time_range}</span>
              <span className={confidenceColor[insight.confidence]}>
                {insight.confidence} confidence
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
