import { motion, AnimatePresence } from "framer-motion";
import { AGENT_MAP, TIER_COLORS } from "../../constants/agents";

interface Props {
  speaking: boolean;
  agentId: string | null;
}

const BAR_COUNT = 20;

const BAR_PROFILES = Array.from({ length: BAR_COUNT }, (_, i) => ({
  duration: 0.5 + ((i * 37) % 50) / 100,
  delay: ((i * 53) % 30) / 100,
  minH: 4 + ((i * 17) % 6),
  maxH: 16 + ((i * 29) % 26),
}));

export function SpeakingBar({ speaking, agentId }: Props) {
  const meta = agentId ? AGENT_MAP[agentId] : null;
  const color = agentId === "COPPER" ? "#ffcb94" : meta ? TIER_COLORS[meta.tier] : "#e0985f";
  const label = agentId === "COPPER" ? "COPPER" : meta?.name ?? "COPPER";

  return (
    <AnimatePresence>
      {speaking && (
        <motion.div
          initial={{ y: "100%", opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: "100%", opacity: 0 }}
          transition={{ type: "spring", damping: 22, stiffness: 260 }}
          className="w-full max-w-2xl mx-auto mb-2 rounded-none border border-zinc-800 bg-void-panel px-4 py-2.5 flex items-center gap-3"
        >
          <span className="w-2 h-2 rounded-none flex-shrink-0 animate-pulse" style={{ background: color }} />
          <span className="font-mono text-[10px] tracking-wider text-ink-secondary flex-shrink-0">
            {label} SPEAKING
          </span>
          <div className="flex items-end gap-[3px] h-5 flex-1 justify-center">
            {BAR_PROFILES.map((p, i) => (
              <motion.span
                key={i}
                className="w-[3px] rounded-none"
                style={{ background: color }}
                animate={{ height: [p.minH, p.maxH, p.minH] }}
                transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
              />
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
