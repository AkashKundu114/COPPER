import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Trash2 } from "lucide-react";
import { AGENT_MAP, TIER_COLORS, TIER_LABELS } from "../../constants/agents";
import {
  fetchAgentHistory,
  resetProfile,
  type ProfileResponse,
  type AgentStats,
  type InteractionRecord,
} from "../../lib/api";

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
  const color = TIER_COLORS[meta.tier];

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-2 mb-1">
        <span
          className="w-2.5 h-2.5 rounded-none"
          style={{ background: color }}
        />
        <h3 className="font-display font-semibold text-lg text-white">
          {meta.name}
        </h3>
      </div>
      <p className="text-xs font-mono text-ink-faint mb-1">
        {TIER_LABELS[meta.tier]} · {meta.domain}
      </p>
      <p className="text-sm text-ink-secondary mb-4">{meta.blurb}</p>

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
              </div>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
