import { useState } from "react";
import { motion } from "framer-motion";
import { Layers, RefreshCw } from "lucide-react";
import { automationAPI } from "@/services/api";

export function WindowManager() {
  const [windows, setWindows] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const { data } = await automationAPI.getProcesses();
      setWindows(data.slice(0, 8).map((p: any) => p.name));
    } catch {
      setWindows([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-copper-400" />
          <span className="text-sm font-medium text-gray-400">Running Processes</span>
        </div>
        <button onClick={refresh} disabled={loading}
          className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      <div className="space-y-1">
        {windows.length === 0 && (
          <p className="text-xs text-gray-600 text-center py-3">Click refresh to load</p>
        )}
        {windows.map((name, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-dark-600 transition-colors">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500/60" />
            <span className="text-xs text-gray-300 truncate">{name}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
