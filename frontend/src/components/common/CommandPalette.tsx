import React, { useEffect, useState } from "react";
import {
  Search,
  LayoutDashboard,
  Radio,
  MessageSquare,
  Bot,
  Brain,
  BarChart3,
  Sparkles,
  Settings,
  Shield,
  Calendar,
  CheckSquare,
  Layers,
  Activity,
  TrendingUp,
  UtensilsCrossed,
} from "lucide-react";
import type { NavSection } from "../layout/Sidebar";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onSelectSection: (section: NavSection) => void;
}

interface CommandItem {
  label: string;
  section: NavSection;
  icon: React.ElementType;
  keywords?: string;
  category: string;
}

const COMMAND_LIST: CommandItem[] = [
  {
    label: "Ops Center Dashboard",
    section: "dashboard",
    icon: LayoutDashboard,
    category: "Command",
    keywords: "home overview telemetry status telemetry",
  },
  {
    label: "Companion HUD (Continuous Voice / VAD)",
    section: "companion",
    icon: Radio,
    category: "Command",
    keywords: "voice holographic audio handsfree mic live vad",
  },
  {
    label: "Conversation & Multi-Agent Chat",
    section: "chat",
    icon: MessageSquare,
    category: "Command",
    keywords: "chat talk message ask assistant prompt",
  },
  {
    label: "Agent Registry & Orchestrator",
    section: "agents",
    icon: Bot,
    category: "Cognitive Mesh",
    keywords: "models mesh swarm subagents routing",
  },
  {
    label: "Memory Center & Knowledge Graph",
    section: "memory",
    icon: Brain,
    category: "Cognitive Mesh",
    keywords: "graph episodic semantic atlas recall memory",
  },
  {
    label: "System Benchmarks & Metrics",
    section: "benchmarks",
    icon: BarChart3,
    category: "Cognitive Mesh",
    keywords: "latency accuracy evaluation throughput tests",
  },
  {
    label: "Autonomous Self-Improvement & LoRA",
    section: "self-improvement",
    icon: Sparkles,
    category: "Cognitive Mesh",
    keywords: "training adapters feedback dpo fine-tuning",
  },
  {
    label: "Security Center & Air-Gap Audit",
    section: "security",
    icon: Shield,
    category: "Cognitive Mesh",
    keywords: "guardian airgap permissions defenses audit",
  },
  {
    label: "Today & Daily Schedule",
    section: "today",
    icon: Calendar,
    category: "Mission Ops",
    keywords: "calendar events agenda day plan schedule",
  },
  {
    label: "Tasks & Objective Queue",
    section: "tasks",
    icon: CheckSquare,
    category: "Mission Ops",
    keywords: "todo action items backlog priorities queue",
  },
  {
    label: "Projects & Workspaces",
    section: "projects",
    icon: Layers,
    category: "Mission Ops",
    keywords: "repositories workspace files deliverables",
  },
  {
    label: "Activity Stream & Audit Log",
    section: "activity",
    icon: Activity,
    category: "Mission Ops",
    keywords: "history logs timeline events telemetry audit",
  },
  {
    label: "System Insights & Trends",
    section: "insights",
    icon: TrendingUp,
    category: "Mission Ops",
    keywords: "analytics patterns performance overview trends",
  },
  {
    label: "Nutrition, Meal & Bio Tracker",
    section: "food",
    icon: UtensilsCrossed,
    category: "Mission Ops",
    keywords: "calories food diet health macro nutrients bio",
  },
  {
    label: "System Settings & Diagnostics",
    section: "settings",
    icon: Settings,
    category: "System",
    keywords: "config preferences developer mode telemetry options",
  },
];

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  open,
  onClose,
  onSelectSection,
}) => {
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (open) onClose();
        else setQuery("");
      }
      if (e.key === "Escape" && open) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const commands = COMMAND_LIST.filter(
    (c) =>
      c.label.toLowerCase().includes(query.toLowerCase()) ||
      c.section.toLowerCase().includes(query.toLowerCase()) ||
      (c.keywords && c.keywords.toLowerCase().includes(query.toLowerCase())),
  );

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-start justify-center pt-24 select-none">
      <div className="w-full max-w-xl bg-bg-panel border border-accent/30 rounded-xl shadow-xl overflow-hidden">
        {}
        <div className="flex items-center px-4 py-3 border-b border-border gap-3">
          <Search size={18} className="text-molten" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search section..."
            autoFocus
            className="w-full bg-transparent border-none outline-none text-text text-sm placeholder-text-muted font-mono"
          />
          <kbd className="px-2 py-0.5 rounded bg-bg text-[10px] text-text-muted border border-border font-mono">
            ESC
          </kbd>
        </div>

        {}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {commands.length > 0 ? (
            commands.map((cmd, idx) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    onSelectSection(cmd.section);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-zinc-300 hover:bg-cyber-cyan/10 hover:text-white hover:border-cyber-cyan/30 border border-transparent transition-all text-left group"
                >
                  <div className="flex items-center gap-3 truncate">
                    <div className="p-1.5 rounded-md bg-white/5 border border-white/10 group-hover:border-cyber-cyan/40 group-hover:bg-cyber-cyan/15 transition-all flex-shrink-0">
                      <Icon
                        size={14}
                        className="text-zinc-400 group-hover:text-cyber-cyan transition-colors"
                      />
                    </div>
                    <div className="flex flex-col truncate">
                      <span className="font-medium text-[12.5px] truncate text-white">{cmd.label}</span>
                      <span className="text-[10px] text-zinc-500 font-mono">{cmd.category}</span>
                    </div>
                  </div>
                  <span className="text-[9.5px] text-cyber-cyan/80 font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-cyber-cyan/10 border border-cyber-cyan/20 ml-2 flex-shrink-0">
                    {cmd.section}
                  </span>
                </button>
              );
            })
          ) : (
            <div className="p-4 text-center text-xs text-text-muted font-mono">
              No matching commands found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
