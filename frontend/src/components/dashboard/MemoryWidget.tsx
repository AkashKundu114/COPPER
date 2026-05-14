import { motion } from "framer-motion";
import { MemoryStick } from "lucide-react";
import { useSystemStats } from "@/hooks/useSystemStats";

export function MemoryWidget() {
  const { stats } = useSystemStats(5000);
  const pct = stats?.memory_percent ?? 0;
  const used = stats?.memory_used_gb ?? 0;
  const total = stats?.memory_total_gb ?? 0;
  const color = pct > 85 ? "#ef4444" : pct > 65 ? "#f59e0b" : "#22d3ee";

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <MemoryStick size={16} className="text-cyan-400" />
        <span className="text-sm font-medium text-gray-400">Memory</span>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-gray-400">
          <span>{used.toFixed(1)} GB used</span>
          <span>{total.toFixed(1)} GB total</span>
        </div>
        <div className="h-2 rounded-full bg-dark-600 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: color, width: `${pct}%` }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <div className="text-right text-xs font-mono" style={{ color }}>{pct.toFixed(1)}%</div>
      </div>
    </motion.div>
  );
}
