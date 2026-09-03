import React from "react";
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  Brain,
  BarChart3,
  Sparkles,
  Settings,
} from "lucide-react";

export type NavSection =
  | "dashboard"
  | "chat"
  | "today"
  | "tasks"
  | "projects"
  | "memory"
  | "agents"
  | "activity"
  | "insights"
  | "benchmarks"
  | "self-improvement"
  | "security"
  | "food"
  | "settings";

interface SidebarProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
}

const NAV_ITEMS: { id: NavSection; label: string; icon: React.ElementType }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "chat", label: "Conversation", icon: MessageSquare },
  { id: "agents", label: "Agent Registry", icon: Bot },
  { id: "memory", label: "Memory Center", icon: Brain },
  { id: "benchmarks", label: "Benchmarks & Metrics", icon: BarChart3 },
  { id: "self-improvement", label: "Self-Improvement", icon: Sparkles },
  { id: "settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
}) => {
  return (
    <aside className="w-60 h-screen bg-[#05080e]/95 backdrop-blur-2xl border-r border-cyber-cyan/20 flex flex-col justify-between p-3 z-30 select-none shadow-[16px_0_40px_rgba(0,0,0,0.5)] font-mono flex-shrink-0">
      <div className="flex-1 flex flex-col min-h-0">
        {/* Brand & Classification Header */}
        <div className="drag-region px-2.5 py-2.5 mb-2 border-b border-cyber-cyan/15 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="notch-corner w-8 h-8 bg-gradient-to-br from-cyber-cyan to-accent text-black flex items-center justify-center font-display font-black text-sm shadow-[0_0_12px_rgba(0,240,255,0.4)] flex-shrink-0">
              C
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center gap-1.5">
                <h1 className="font-display font-bold text-[14px] tracking-tight text-white truncate">
                  C.O.P.P.E.R.
                </h1>
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-ping flex-shrink-0" />
              </div>
              <p className="text-[9px] text-cyber-cyan font-mono tracking-wider uppercase truncate">
                GOD'S EYE OPS // TIER-1
              </p>
            </div>
          </div>

          <div className="mt-2 px-2 py-0.5 rounded bg-black/60 border border-cyber-cyan/20 flex items-center justify-between text-[9px] text-zinc-400">
            <span className="text-verdigris font-bold">AIR-GAPPED</span>
            <span className="text-zinc-500">26 MODELS</span>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav className="no-drag space-y-0.5 overflow-y-auto flex-1 custom-scrollbar pr-1 min-h-0">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-150 group ${
                  isActive
                    ? "copper-trace bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/40 shadow-sm"
                    : "text-zinc-400 border border-transparent hover:text-white hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <Icon
                    className={`w-[14px] h-[14px] flex-shrink-0 transition-colors ${
                      isActive
                        ? "text-cyber-cyan drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]"
                        : "text-zinc-500 group-hover:text-zinc-300"
                    }`}
                  />
                  <span className="tracking-tight truncate">{item.label}</span>
                </div>
                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full bg-cyber-cyan shadow-[0_0_8px_rgba(0,240,255,0.8)] flex-shrink-0 ml-1" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry & Air-Gap Status Panel */}
      <div className="p-2 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1 font-mono text-[9px] flex-shrink-0 mt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-verdigris shadow-[0_0_8px_rgba(0,255,136,0.6)] animate-pulse flex-shrink-0" />
            <span className="font-bold text-white tracking-wider">
              100% OFFLINE
            </span>
          </div>
          <span className="text-zinc-500">0.05ms</span>
        </div>

        <div className="w-full bg-zinc-900 rounded-full h-1 overflow-hidden border border-white/5">
          <div className="bg-gradient-to-r from-cyber-cyan to-accent h-full w-[80%]" />
        </div>

        <div className="flex justify-between text-[9px] text-zinc-400">
          <span>VRAM: 6.4/8.0 GB</span>
          <span className="text-verdigris font-semibold">PASS</span>
        </div>
      </div>
    </aside>
  );
};
