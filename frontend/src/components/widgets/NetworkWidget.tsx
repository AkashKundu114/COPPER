import { Activity } from "lucide-react";

interface Props {
  connected: boolean;
  agentsMet: number;
  agentsTotal: number;
}

export function NetworkWidget({ connected, agentsMet, agentsTotal }: Props) {
  return (
    <div className="rounded-xl border border-copper-dim/40 bg-void-panel/70 backdrop-blur-md px-4 py-3 min-w-[150px]">
      <div className="flex items-center gap-2 mb-1.5">
        <Activity size={14} className={connected ? "text-copper-hot" : "text-ink-faint"} />
        <span className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">Network</span>
      </div>
      <p className="text-sm text-ink-primary">
        {connected ? "All agents online" : "Reconnecting…"}
      </p>
      <p className="font-mono text-[10px] text-ink-secondary mt-0.5">
        {agentsMet}/{agentsTotal} agents acquainted
      </p>
    </div>
  );
}
