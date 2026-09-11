import React from "react";
import {
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

export type NavSection =
  | "dashboard"
  | "companion"
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

interface NavGroup {
  category: string;
  items: { id: NavSection; label: string; icon: React.ElementType }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    category: "COMMAND & HUD",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      { id: "companion", label: "Companion HUD", icon: Radio },
      { id: "chat", label: "Conversation", icon: MessageSquare },
    ],
  },
  {
    category: "COGNITIVE MESH",
    items: [
      { id: "agents", label: "Agent Registry", icon: Bot },
      { id: "memory", label: "Memory Center", icon: Brain },
      { id: "benchmarks", label: "Benchmarks", icon: BarChart3 },
      { id: "self-improvement", label: "Self-Improvement", icon: Sparkles },
      { id: "security", label: "Security Center", icon: Shield },
    ],
  },
  {
    category: "MISSION OPS",
    items: [
      { id: "today", label: "Today & Schedule", icon: Calendar },
      { id: "tasks", label: "Tasks & Queue", icon: CheckSquare },
      { id: "projects", label: "Projects", icon: Layers },
      { id: "activity", label: "Activity Stream", icon: Activity },
      { id: "insights", label: "System Insights", icon: TrendingUp },
      { id: "food", label: "Nutrition & Bio", icon: UtensilsCrossed },
    ],
  },
  {
    category: "SYSTEM",
    items: [
      { id: "settings", label: "Settings", icon: Settings },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
}) => {
  return (
    <aside
      aria-label="Main Navigation"
      className="w-64 h-screen bg-[#0a0f19]/85 backdrop-blur-2xl border-r border-white/[0.08] flex flex-col justify-between p-3 z-30 select-none shadow-[16px_0_48px_rgba(0,0,0,0.28)] font-mono flex-shrink-0"
    >
      <div className="flex-1 flex flex-col min-h-0">
        {/* Brand & Classification Header */}
        <div className="drag-region px-3 py-3 mb-2 border-b border-white/[0.07] flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyber-cyan via-[#53c9e5] to-accent text-black flex items-center justify-center font-display font-black text-sm shadow-[0_8px_22px_rgba(0,240,255,0.25)] flex-shrink-0" aria-hidden="true">
              C
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center gap-1.5">
                <h1 className="font-display font-bold text-[14px] tracking-tight text-white truncate">
                  C.O.P.P.E.R.
                </h1>
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-ping flex-shrink-0" aria-hidden="true" />
              </div>
              <p className="text-[9px] text-cyber-cyan/80 font-mono tracking-[0.14em] uppercase truncate">
                PERSONAL INTELLIGENCE
              </p>
            </div>
          </div>

          <div className="mt-3 px-2.5 py-1 rounded-lg bg-white/[0.035] border border-white/[0.07] flex items-center justify-between text-[9px] text-zinc-300">
            <span className="text-verdigris font-bold">AIR-GAPPED</span>
            <span className="text-zinc-400">26 MODELS</span>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav aria-label="Application Sections" className="no-drag space-y-3 overflow-y-auto flex-1 custom-scrollbar pr-1 min-h-0">
          {NAV_GROUPS.map((group) => (
            <div key={group.category} className="space-y-1">
              <div className="px-2.5 py-1 text-[8.5px] font-mono font-semibold tracking-[0.14em] text-zinc-500 uppercase flex items-center justify-between">
                <span>{group.category}</span>
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectSection(item.id)}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={`${item.label} section${isActive ? ", current page" : ""}`}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-[12px] font-medium transition-all duration-200 group cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-cyan ${
                      isActive
                        ? "bg-gradient-to-r from-cyber-cyan/18 to-cyber-cyan/[0.04] text-cyber-cyan border border-cyber-cyan/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_6px_18px_rgba(0,240,255,0.06)]"
                        : "text-zinc-300 border border-transparent hover:text-white hover:bg-white/[0.055] hover:translate-x-0.5"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon
                        aria-hidden="true"
                        className={`w-[14px] h-[14px] flex-shrink-0 transition-colors ${
                          isActive
                            ? "text-cyber-cyan drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]"
                            : "text-zinc-400 group-hover:text-zinc-200"
                        }`}
                      />
                      <span className="tracking-tight truncate">{item.label}</span>
                    </div>
                    {isActive && (
                      <div className="w-1.5 h-1.5 rounded-full bg-cyber-cyan shadow-[0_0_8px_rgba(0,240,255,0.8)] flex-shrink-0 ml-1" aria-hidden="true" />
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Bottom Telemetry & Air-Gap Status Panel */}
      <div className="p-2.5 rounded-xl bg-white/[0.035] border border-white/[0.08] space-y-1.5 font-mono text-[9px] flex-shrink-0 mt-2 shadow-inner">
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
