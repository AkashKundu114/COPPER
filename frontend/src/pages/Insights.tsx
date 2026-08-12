import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { memoryAPI } from "@/services/api";

interface Insight {
  text: string;
  sample_size: number;
  time_range: string;
  confidence: "high" | "medium" | "low";
}

export default function Insights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Insights are derived from structured memories (UserMemoryV2, category="observation").
    // Endpoint lands with the pass-5 migration; until then this renders the empty state
    // rather than fabricating data (Master UI Prompt §28: "never fabricate statistics").
    memoryAPI.getStats()
      .then(() => setInsights([]))
      .finally(() => setLoading(false));
  }, []);

  const confidenceColor = { high: "text-green-400", medium: "text-amber-400", low: "text-gray-500" };

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2">
        <TrendingUp size={20} className="text-copper-400" />
        <h2 className="font-semibold text-white">Insights</h2>
      </div>
      <p className="text-xs text-gray-500">
        Evidence-based patterns only. Every insight shows its sample size and confidence —
        nothing here is fabricated.
      </p>

      {loading && <p className="text-sm text-gray-600 text-center py-8">Loading…</p>}
      {!loading && insights.length === 0 && (
        <p className="text-sm text-gray-600 text-center py-12">
          Not enough observed data yet. Insights appear once COPPER has evidence to back them.
        </p>
      )}

      <div className="space-y-2">
        {insights.map((insight, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl p-4">
            <p className="text-sm text-gray-200">{insight.text}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>{insight.sample_size} data points</span>
              <span>{insight.time_range}</span>
              <span className={confidenceColor[insight.confidence]}>
                {insight.confidence} confidence
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
