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
  const [selectedIndex, setSelectedIndex] = useState(0);

  const commands = COMMAND_LIST.filter(
    (c) =>
      c.label.toLowerCase().includes(query.toLowerCase()) ||
      c.section.toLowerCase().includes(query.toLowerCase()) ||
      (c.keywords && c.keywords.toLowerCase().includes(query.toLowerCase())),
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (open) onClose();
        else {
          setQuery("");
          setSelectedIndex(0);
        }
      }
      if (e.key === "Escape" && open) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (commands.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % commands.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + commands.length) % commands.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (commands[selectedIndex]) {
        onSelectSection(commands[selectedIndex].section);
        onClose();
      }
    }
  };

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
      className="fixed inset-0 bg-[#0D0407]/80 backdrop-blur-md z-50 flex items-start justify-center pt-24 select-none p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-[#1A0A0F]/95 backdrop-blur-2xl border border-blush-100/20 rounded-2xl shadow-[0_24px_64px_rgba(10,3,6,0.65),inset_0_1px_0_rgba(246,230,234,0.14)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 py-3.5 border-b border-blush-100/10 gap-3">
          <Search size={18} className="text-blush-100" aria-hidden="true" />
          <input
            type="text"
            role="combobox"
            aria-expanded="true"
            aria-autocomplete="list"
            aria-controls="command-palette-list"
            aria-activedescendant={commands[selectedIndex] ? `command-item-${selectedIndex}` : undefined}
            aria-label="Type a command or search section"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Type a command or search section..."
            autoFocus
            className="w-full bg-transparent border-none outline-none text-white text-sm placeholder-blush-300/40 font-mono"
          />
          <kbd className="px-2 py-0.5 rounded-md bg-[#280F19] text-[10px] text-blush-200 border border-blush-100/20 font-mono font-bold" aria-label="Escape key to close">
            ESC
          </kbd>
        </div>

        <div
          id="command-palette-list"
          role="listbox"
          aria-label="Command suggestions"
          className="max-h-80 overflow-y-auto p-2 space-y-1 custom-scrollbar"
        >
          {commands.length > 0 ? (
            commands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = selectedIndex === idx;
              return (
                <button
                  key={idx}
                  id={`command-item-${idx}`}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => {
                    onSelectSection(cmd.section);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all text-left group cursor-pointer focus-visible:ring-2 focus-visible:ring-blush-100 ${
                    isSelected
                      ? "bg-gradient-to-r from-blush-100/18 via-accent/10 to-transparent text-white border border-blush-100/30 shadow-[inset_0_1px_0_rgba(246,230,234,0.15)]"
                      : "text-zinc-300 hover:bg-blush-100/[0.05] border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3 truncate">
                    <div className={`p-1.5 rounded-lg border transition-all flex-shrink-0 ${
                      isSelected
                        ? "border-blush-100/40 bg-blush-100/20 text-blush-100 shadow-[0_0_10px_rgba(246,230,234,0.3)]"
                        : "bg-white/[0.04] border-blush-100/10 text-zinc-400 group-hover:border-blush-100/30 group-hover:text-blush-100"
                    }`}>
                      <Icon size={14} aria-hidden="true" />
                    </div>
                    <div className="flex flex-col truncate">
                      <span className="font-medium text-[13px] truncate text-white">{cmd.label}</span>
                      <span className="text-[10px] text-blush-300/50 font-mono">{cmd.category}</span>
                    </div>
                  </div>
                  <span className="text-[9.5px] text-blush-100/90 font-mono uppercase tracking-wider px-2 py-0.5 rounded-md bg-blush-100/10 border border-blush-100/20 ml-2 flex-shrink-0 font-semibold">
                    {cmd.section}
                  </span>
                </button>
              );
            })
          ) : (
            <div className="p-4 text-center text-xs text-blush-300/50 font-mono" role="status">
              No matching commands found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
