import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Trash2, Cpu } from "lucide-react";
import { AGENT_MAP, TIER_COLORS, TIER_LABELS } from "../../constants/agents";
import { AgentIcon } from "../chat/AgentIcon";
import {
  fetchAgentHistory,
  resetProfile,
  type ProfileResponse,
  type AgentStats,
  type InteractionRecord,
} from "../../lib/api";
import { selfMemoryAPI } from "../../services/api";

interface Props {
  open: boolean;
  onClose: () => void;
  profile: ProfileResponse | null;
  agentStats: Record<string, AgentStats>;
  selectedAgent: string | null;
  onProfileReset: () => void;
}

function FactRow({
  label,
  value,
  confidence,
}: {
  label: string;
  value: string;
  confidence: number;
}) {
  return (
    <div className="py-2 border-b border-zinc-800 last:border-0">
      <div className="flex items-center justify-between mb-1">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">
          {label.replace(/_/g, " ")}
        </span>
        <span className="font-mono text-[10px] text-ink-faint">
          {Math.round(confidence * 100)}%
        </span>
      </div>
      <p className="text-sm text-white">{value}</p>
      <div className="h-1 mt-1.5 rounded-none bg-zinc-900 border border-zinc-800 overflow-hidden">
        <div
          className="h-full bg-white"
          style={{ width: `${confidence * 100}%` }}
        />
      </div>
    </div>
  );
}

function AgentDetail({
  agentId,
  stats,
}: {
  agentId: string;
  stats?: AgentStats;
}) {
  const [history, setHistory] = useState<InteractionRecord[]>([]);
  const meta = AGENT_MAP[agentId];

  useEffect(() => {
    fetchAgentHistory(agentId, 15)
      .then(setHistory)
      .catch(() => setHistory([]));
  }, [agentId]);

  if (!meta) return null;
  const color = meta.color || TIER_COLORS[meta.tier] || "#06b6d4";

  return (
    <div className="animate-fade-in space-y-4">
      <div className="flex items-center gap-3 p-3 rounded-2xl border" style={{ backgroundColor: `${color}15`, borderColor: `${color}40` }}>
        <div
          className="p-2.5 rounded-xl border flex items-center justify-center shadow-inner"
          style={{
            backgroundColor: `${color}25`,
            borderColor: `${color}60`,
            color: color,
          }}
        >
          <AgentIcon agentId={agentId} size={22} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-display font-semibold text-lg text-white">
              {meta.name}
            </h3>
            <span className="text-[10px] font-mono text-zinc-400">
              [{meta.id}]
            </span>
          </div>
          <p className="text-xs font-semibold" style={{ color }}>
            {meta.domain}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-mono px-1">
        <span className="text-zinc-400">{TIER_LABELS[meta.tier]}</span>
        <span className="text-zinc-300 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded-md flex items-center gap-1">
          <Cpu size={10} className="text-zinc-400" />
          {meta.model}
        </span>
      </div>

      <p className="text-sm text-ink-secondary leading-relaxed bg-void-raised p-3 rounded-xl border border-zinc-800/80">{meta.blurb}</p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-none bg-void-raised border border-zinc-800 px-3 py-2">
          <p className="font-mono text-[10px] text-ink-faint uppercase">
            Familiarity
          </p>
          <p className="text-sm text-white">
            {stats?.familiarity_tier ?? "Stranger"}
          </p>
        </div>
        <div className="rounded-none bg-void-raised border border-zinc-800 px-3 py-2">
          <p className="font-mono text-[10px] text-ink-faint uppercase">
            Jobs handled
          </p>
          <p className="text-sm text-white">{stats?.times_invoked ?? 0}</p>
        </div>
      </div>

      <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint mb-2">
        Job log — this node's memory
      </p>
      {history.length === 0 && (
        <p className="text-sm text-ink-faint italic">
          No jobs logged yet for this agent.
        </p>
      )}
      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {history.map((h) => (
          <div
            key={h.id}
            className="rounded-none bg-void-raised border border-zinc-850 px-3 py-2"
          >
            <p className="text-xs text-ink-secondary line-clamp-2">
              {h.user_message}
            </p>
            <p className="text-xs text-white mt-1">{h.response}</p>
            <p className="font-mono text-[9px] text-ink-faint mt-1">
              {h.timestamp}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SideDrawer({
  open,
  onClose,
  profile,
  agentStats,
  selectedAgent,
  onProfileReset,
}: Props) {
  const [drawerTab, setDrawerTab] = useState<'profile' | 'mind'>('profile');
  const [selfMemories, setSelfMemories] = useState<any[]>([]);

  useEffect(() => {
    if (open && !selectedAgent && drawerTab === 'mind') {
      selfMemoryAPI.getAll().then(setSelfMemories).catch(console.error);
    }
  }, [open, selectedAgent, drawerTab]);

  const resolveMemory = async (id: string) => {
    try {
      await selfMemoryAPI.resolve(id);
      const data = await selfMemoryAPI.getAll();
      setSelfMemories(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleReset = async () => {
    if (
      !confirm(
        "This clears everything COPPER has learned about you and every agent's memory. Continue?",
      )
    )
      return;
    await resetProfile();
    onProfileReset();
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          initial={{ x: 360, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 360, opacity: 0 }}
          transition={{ type: "spring", damping: 28, stiffness: 260 }}
          className="fixed top-0 right-0 h-full w-[360px] bg-void-panel border-l border-zinc-800 z-40 overflow-y-auto"
        >
          <div className="p-5">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Brain size={16} className="text-white" />
                <h2 className="font-display font-semibold text-white">
                  {selectedAgent ? "Agent Node" : "What COPPER knows"}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="text-ink-faint hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {selectedAgent ? (
              <AgentDetail
                agentId={selectedAgent}
                stats={agentStats[selectedAgent]}
              />
            ) : (
              <div className="animate-fade-in">
                <div className="flex gap-1 p-1 bg-bg-panel rounded-lg mb-4">
                  <button
                    onClick={() => setDrawerTab('profile')}
                    className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      drawerTab === 'profile'
                        ? 'bg-verdigris-900/60 text-verdigris-300'
                        : 'text-ink-muted hover:text-ink-secondary'
                    }`}
                  >
                    What COPPER knows
                  </button>
                  <button
                    onClick={() => setDrawerTab('mind')}
                    className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      drawerTab === 'mind'
                        ? 'bg-verdigris-900/60 text-verdigris-300'
                        : 'text-ink-muted hover:text-ink-secondary'
                    }`}
                  >
                    COPPER's Mind
                  </button>
                </div>

                {drawerTab === 'profile' ? (
                  <>
                    <div className="rounded-none border border-zinc-800 bg-void-raised px-4 py-3 mb-4">
                      <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint mb-1">
                        Relationship
                      </p>
                      <p className="font-display text-lg text-white font-semibold">
                        {profile?.relationship_tier ?? "Just Met"}
                      </p>
                      <p className="text-xs text-ink-secondary mt-1">
                        {profile?.total_interactions ?? 0} interactions ·{" "}
                        {profile?.agents_met ?? 0}/{profile?.agents_total ?? 50}{" "}
                        agents met
                      </p>
                      {profile?.most_used_agent && (
                        <p className="text-xs text-ink-secondary mt-0.5">
                          Most trusted:{" "}
                          <span className="text-ink-primary">
                            {AGENT_MAP[profile.most_used_agent]?.name}
                          </span>
                        </p>
                      )}
                    </div>

                    <p className="font-mono text-[10px] uppercase tracking-wider text-ink-faint mb-2">
                      Learned facts
                    </p>
                    {(!profile || profile.facts.length === 0) && (
                      <p className="text-sm text-ink-faint italic mb-4">
                        Nothing yet — the more you talk, the more it picks up.
                      </p>
                    )}
                    <div className="mb-6">
                      {profile?.facts.map((f) => (
                        <FactRow
                          key={f.key}
                          label={f.key}
                          value={f.value}
                          confidence={f.confidence}
                        />
                      ))}
                    </div>

                    <button
                      onClick={handleReset}
                      className="flex items-center gap-2 text-xs font-mono text-ink-faint hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={13} /> Forget everything
                    </button>
                  </>
                ) : (
                  <div className="animate-fade-in space-y-2">
                    {selfMemories.length === 0 && (
                      <p className="text-sm text-ink-faint italic mb-4">
                        Mind is quiet...
                      </p>
                    )}
                    {selfMemories.map((mem) => (
                      <div key={mem.id} className="p-3 bg-bg-raised rounded-lg border border-white/5 mb-2">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-1.5 py-0.5 text-[10px] font-bold uppercase rounded ${
                              mem.category === 'correction' ? 'bg-molten-950 text-molten-400 border border-molten-800/40' :
                              mem.category === 'open_question' ? 'bg-blue-950 text-blue-400 border border-blue-800/40 border-dashed' :
                              'bg-verdigris-950 text-verdigris-400 border border-verdigris-800/40'
                          }`}>{mem.category?.replace('_', ' ')}</span>
                          {mem.category === 'correction' && (
                              <span className="text-[10px] text-molten-400">Learned from you</span>
                          )}
                          {mem.category === 'open_question' && !mem.outcome && (
                              <span className="text-[10px] text-blue-400 italic">Still thinking...</span>
                          )}
                        </div>
                        <p className="text-xs text-ink-default leading-relaxed">{mem.content}</p>
                        <div className="flex items-center justify-between mt-2 text-[10px] text-ink-muted">
                            <span>{Math.round(mem.confidence * 100)}% · {mem.evidence_count}x</span>
                            <span>{new Date(mem.created_at).toLocaleDateString()}</span>
                        </div>
                        {mem.category === 'open_question' && !mem.outcome && (
                            <button
                                onClick={() => resolveMemory(mem.id)}
                                className="mt-2 px-2 py-1 text-[10px] text-verdigris-400 border border-verdigris-800/40 rounded hover:bg-verdigris-950/40 transition-colors"
                            >
                                Mark as resolved
                            </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
