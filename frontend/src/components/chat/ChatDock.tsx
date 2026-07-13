import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TIER_COLORS, AGENT_MAP } from "../../data/agents";
import type { ChatLine } from "../../lib/useBrainSocket";

interface Props {
  lines: ChatLine[];
  connected: boolean;
  thinking: boolean;
  onSend: (message: string) => void;
}

function lineColor(agentId: string): string {
  if (agentId === "YOU") return "#f3ece2";
  if (agentId === "COPPER") return "#ffcb94";
  return TIER_COLORS[AGENT_MAP[agentId]?.tier] ?? "#e0985f";
}

export function ChatDock({ lines, connected, thinking, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [lines.length]);

  const submit = () => {
    const msg = draft.trim();
    if (!msg) return;
    onSend(msg);
    setDraft("");
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {lines.length > 0 && (
        <div
          ref={scrollRef}
          className="mb-2 max-h-56 overflow-y-auto rounded-xl border border-copper-dim/40 bg-void-panel/80 backdrop-blur-md px-4 py-3 space-y-2"
        >
          <AnimatePresence initial={false}>
            {lines.map((line) => (
              <motion.div
                key={line.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex flex-col ${line.agent === "YOU" ? "items-end" : "items-start"}`}
              >
                <span className="font-mono text-[10px] tracking-wide opacity-60" style={{ color: lineColor(line.agent) }}>
                  {line.agent}
                </span>
                <span className="text-sm text-ink-primary font-body max-w-[85%]">{line.text}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <div className="flex items-center gap-2 rounded-2xl border border-copper-dim/50 bg-void-panel/90 backdrop-blur-md px-3 py-2 shadow-[0_0_30px_rgba(184,115,51,0.08)]">
        <span
          className={`w-2 h-2 rounded-full flex-shrink-0 ${connected ? "bg-copper-hot" : "bg-ink-faint"}`}
          title={connected ? "Connected" : "Reconnecting…"}
        />
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder={thinking ? "COPPER is thinking…" : "Tell COPPER what you need…"}
          className="flex-1 bg-transparent outline-none text-sm font-body text-ink-primary placeholder:text-ink-faint"
        />
        <button
          onClick={submit}
          disabled={!draft.trim()}
          className="px-3 py-1.5 rounded-lg bg-copper-base/20 hover:bg-copper-base/35 text-copper-flare text-xs font-mono tracking-wide transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        >
          SEND
        </button>
      </div>
    </div>
  );
}
