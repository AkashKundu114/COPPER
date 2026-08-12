import { useEffect, useState } from "react";
import { Cpu, RotateCcw, Power, CheckCircle2 } from "lucide-react";
import { fetchAgents, type AgentStats } from "../lib/api";

export function AgentRegistry() {
  const [agents, setAgents] = useState<AgentStats[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await fetchAgents();
      setAgents(data);
    } catch {
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div className="flex items-center gap-2">
        <Cpu size={20} className="text-[#ff5722]" />
        <h1 className="text-xl font-bold text-white tracking-tight">Agent Registry</h1>
      </div>
      <p className="text-xs text-gray-400 font-mono">
        Versioned, hot-swappable agents. Rollback restores the previous checkpoint without data loss.
      </p>

      {loading && <p className="text-sm text-gray-400 text-center py-8 font-mono">Loading active agents...</p>}
      {!loading && agents.length === 0 && (
        <div className="p-6 rounded-xl bg-[#14141a] border border-white/10 text-center text-xs text-gray-400 font-mono space-y-2">
          <p>No external dynamic agents registered yet. All 30 COPPER core agents active offline.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {agents.map((a) => (
          <div key={a.id} className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-semibold text-white text-sm">{a.name}</p>
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-mono">
                <CheckCircle2 size={12} /> Active
              </span>
            </div>
            <p className="text-xs text-gray-400 font-mono">
              Tier: {a.tier} · Invocations: {a.times_invoked}
            </p>
            <div className="flex gap-2 pt-1 font-mono text-xs">
              <button className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-black/40 border border-white/10 text-gray-300 hover:text-white transition-colors">
                <RotateCcw size={12} /> Rollback
              </button>
              <button className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg bg-black/40 border border-red-500/30 text-red-400 hover:bg-red-950/40 transition-colors">
                <Power size={12} /> Disable
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
