import { motion } from "framer-motion";
import { Cpu } from "lucide-react";
import { useSystemStats } from "@/hooks/useSystemStats";

function Arc({ percent, color }: { percent: number; color: string }) {
  const r = 28, c = 2 * Math.PI * r;
  const dash = (percent / 100) * c;
  return (
    <svg className="w-20 h-20 -rotate-90" viewBox="0 0 64 64">
      <circle cx="32" cy="32" r={r} fill="none" stroke="#1a1a28" strokeWidth="6" />
      <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
        style={{ transition: "stroke-dasharray 0.5s ease" }} />
    </svg>
  );
}

export function CpuWidget() {
  const { stats } = useSystemStats(3000);
  const cpu = stats?.cpu_percent ?? 0;
  const color = cpu > 80 ? "#ef4444" : cpu > 60 ? "#f59e0b" : "#ff7c1f";

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Cpu size={16} className="text-copper-400" />
        <span className="text-sm font-medium text-gray-400">CPU</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Arc percent={cpu} color={color} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-white">{cpu.toFixed(0)}%</span>
          </div>
        </div>
        <div className="text-xs text-gray-500 space-y-1">
          <div>OS: <span className="text-gray-300">{stats?.os ?? "—"}</span></div>
        </div>
      </div>
    </motion.div>
  );
}
