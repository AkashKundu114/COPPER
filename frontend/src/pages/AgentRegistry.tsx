import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cpu, RotateCcw, Power, CheckCircle2 } from "lucide-react";
import { agentRegistryAPI } from "@/services/api";

interface AgentVersion {
  id: number;
  agent_id: string;
  version: string;
  display_name: string;
  model_provider: string;
  model_name: string;
  status: string;
  evaluation_score: number | null;
  is_current: boolean;
}

export default function AgentRegistry() {
  const [agents, setAgents] = useState<AgentVersion[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await agentRegistryAPI.list();
      setAgents(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const rollback = async (agentId: string) => {
    await agentRegistryAPI.rollback(agentId);
    load();
  };

  const disable = async (agentId: string) => {
    await agentRegistryAPI.disable(agentId);
    load();
  };

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2">
        <Cpu size={20} className="text-copper-400" />
        <h2 className="font-semibold text-white">Agent Registry</h2>
      </div>
      <p className="text-xs text-gray-500">
        Versioned, hot-swappable agents. Rollback restores the previous checkpoint without data loss.
      </p>

      {loading && <p className="text-sm text-gray-600 text-center py-8">Loading…</p>}
      {!loading && agents.length === 0 && (
        <p className="text-sm text-gray-600 text-center py-8">No agents registered yet.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {agents.map((a) => (
          <motion.div key={a.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <p className="font-medium text-white text-sm">{a.display_name}</p>
              {a.is_current && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle2 size={12} /> Active
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 font-mono">
              v{a.version} · {a.model_provider}/{a.model_name}
            </p>
            {a.evaluation_score != null && (
              <p className="text-xs text-gray-400">Score: {(a.evaluation_score * 100).toFixed(0)}%</p>
            )}
            <div className="flex gap-2 pt-2">
              <button onClick={() => rollback(a.agent_id)}
                className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-gray-400 text-xs transition-colors">
                <RotateCcw size={12} /> Rollback
              </button>
              <button onClick={() => disable(a.agent_id)}
                className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-dark-700 hover:bg-red-600/20 hover:text-red-400 text-gray-400 text-xs transition-colors">
                <Power size={12} /> Disable
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
