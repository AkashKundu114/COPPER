import React, { useState, useEffect } from "react";
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
  Activity,
  TrendingUp,
  UtensilsCrossed,
  Users,
  Mail,
  Megaphone,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
} from "lucide-react";
import { soundFX } from "../../lib/soundFX";
import { systemAPI } from "../../services/api";
import { AGENTS } from "../../constants/agents";

export type NavSection =
  | "dashboard"
  | "companion"
  | "chat"
  | "today"
  | "meetings"
  | "email"
  | "memory"
  | "agents"
  | "activity"
  | "insights"
  | "benchmarks"
  | "self-improvement"
  | "security"
  | "food"
  | "settings"
  | "campaigns";

interface SidebarProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  onOpenCommandPalette?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

interface NavItem {
  id: NavSection;
  label: string;
  icon: React.ElementType;
  testId?: string;
  ariaLabel?: string;
}

interface NavGroup {
  category: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    category: "WORKSPACE",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      {
        id: "chat",
        label: "Chat",
        icon: MessageSquare,
        testId: "conversation-nav",
        ariaLabel: "AI Chat",
      },
      { id: "companion", label: "Voice", icon: Radio },
      {
        id: "campaigns",
        label: "Campaigns",
        icon: Megaphone,
        testId: "campaigns-nav",
        ariaLabel: "Campaign Intelligence",
      },
    ],
  },
  {
    category: "PRODUCTIVITY",
    items: [
      { id: "today", label: "Today", icon: Calendar },
      { id: "meetings", label: "Meetings", icon: Users },
      { id: "email", label: "Alerts", icon: Mail },
      { id: "food", label: "Wellness", icon: UtensilsCrossed },
    ],
  },
  {
    category: "INTELLIGENCE",
    items: [
      { id: "memory", label: "Memory", icon: Brain },
      { id: "agents", label: "Agents", icon: Bot },
      { id: "benchmarks", label: "Benchmarks", icon: BarChart3 },
      { id: "security", label: "Security", icon: Shield },
      {
        id: "activity",
        label: "Activity",
        icon: Activity,
        testId: "activity-nav",
        ariaLabel: "Activity Log",
      },
      { id: "insights", label: "Insights", icon: TrendingUp },
      { id: "self-improvement", label: "Optimization", icon: Sparkles },
      { id: "settings", label: "Settings", icon: Settings },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
  onOpenCommandPalette,
  isCollapsed: controlledCollapsed,
  onToggleCollapse: controlledToggle,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const toggleCollapse = () => {
    if (controlledToggle) {
      controlledToggle();
    } else {
      setInternalCollapsed((prev) => !prev);
    }
  };

  const [telemetry, setTelemetry] = useState<{
    vramUsed: number;
    vramTotal: number;
    vramPct: number;
  }>({
    vramUsed: 0.22,
    vramTotal: 8.0,
    vramPct: 2.8,
  });

  useEffect(() => {
    const fetchTelem = () => {
      systemAPI
        .getTelemetry()
        .then((res) => {
          if (res.data?.gpu) {
            const gpu = res.data.gpu;
            setTelemetry({
              vramUsed: gpu.vram_used_gb || 0.22,
              vramTotal: gpu.vram_total_gb || 8.0,
              vramPct: gpu.vram_percent || 2.8,
            });
          }
        })
        .catch(() => {});
    };
    fetchTelem();
    const iv = setInterval(fetchTelem, 4000);
    return () => clearInterval(iv);
  }, []);

  return (
    <aside
      aria-label="Main Navigation"
      className={`${
        isCollapsed ? "w-14" : "w-60"
      } h-screen bg-surface-base border-r border-border flex flex-col justify-between p-2.5 z-30 select-none flex-shrink-0 transition-all duration-200`}
    >
      <div className="flex-1 flex flex-col min-h-0">
        {/* Brand & Window Drag Region */}
        <div className="drag-region px-1.5 py-2 mb-2 border-b border-border flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2 overflow-hidden">
            <div
              className="w-7 h-7 rounded-lg bg-copper text-text-inverse flex items-center justify-center font-brand font-bold text-xs shadow-sm flex-shrink-0"
              aria-hidden="true"
            >
              C
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden">
                <div className="flex items-center gap-1.5">
                  <h1 className="font-brand font-bold text-[13px] tracking-tight text-text truncate">
                    COPPER
                  </h1>
                  <span className="w-1.5 h-1.5 rounded-full bg-success flex-shrink-0" aria-hidden="true" />
                </div>
                <p className="text-[8.5px] text-text-tertiary font-mono tracking-wider uppercase truncate">
                  AI WORKSTATION
                </p>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={toggleCollapse}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="no-drag p-1 rounded-md text-text-secondary hover:text-text hover:bg-surface-hover transition-colors cursor-pointer"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? <PanelLeftOpen size={14} /> : <PanelLeftClose size={14} />}
          </button>
        </div>

        {/* Quick Search Shortcut */}
        {onOpenCommandPalette && (
          <div className="no-drag mb-2 px-1 flex-shrink-0">
            <button
              type="button"
              onClick={() => {
                soundFX.play("click");
                onOpenCommandPalette();
              }}
              className={`w-full flex items-center ${
                isCollapsed ? "justify-center p-2" : "justify-between px-2.5 py-1.5"
              } rounded-lg bg-surface-elevated hover:bg-surface-hover border border-border-subtle text-text-secondary hover:text-text text-xs transition-colors cursor-pointer`}
              title="Search or jump to... (Ctrl+K)"
            >
              <div className="flex items-center gap-2">
                <Search size={13} className="text-copper flex-shrink-0" />
                {!isCollapsed && <span className="text-[11px] truncate">Search...</span>}
              </div>
              {!isCollapsed && (
                <kbd className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-surface-base border border-border-subtle text-text-tertiary">
                  Ctrl+K
                </kbd>
              )}
            </button>
          </div>
        )}

        {/* Navigation Sections */}
        <nav
          aria-label="Application Sections"
          className="no-drag space-y-3 overflow-y-auto flex-1 pr-0.5 min-h-0"
        >
          {NAV_GROUPS.map((group) => (
            <div key={group.category} className="space-y-0.5">
              {!isCollapsed && (
                <div className="px-2 py-1 text-[9px] font-mono font-medium tracking-wider text-text-tertiary uppercase">
                  <span>{group.category}</span>
                </div>
              )}
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                const testId = item.testId || `${item.id}-nav`;
                return (
                  <button
                    key={item.id}
                    type="button"
                    data-testid={testId}
                    onClick={() => {
                      soundFX.play("tab");
                      onSelectSection(item.id);
                    }}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={
                      item.ariaLabel ||
                      `${item.label} section${isActive ? ", current page" : ""}`
                    }
                    title={isCollapsed ? item.label : undefined}
                    className={`w-full flex items-center ${
                      isCollapsed ? "justify-center px-1 py-1.5" : "justify-between px-2.5 py-1.5"
                    } rounded-md text-caption font-medium transition-all duration-100 group cursor-pointer ${
                      isActive
                        ? "bg-copper-subtle text-text border-l-2 border-copper font-medium"
                        : "text-text-secondary border-l-2 border-transparent hover:text-text hover:bg-surface-hover"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon
                        aria-hidden="true"
                        className={`w-4 h-4 flex-shrink-0 transition-colors ${
                          isActive ? "text-copper" : "text-text-secondary group-hover:text-text"
                        }`}
                      />
                      {!isCollapsed && (
                        <span className="tracking-tight truncate">{item.label}</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Bottom Telemetry & Status Panel */}
      <div className="rounded-lg bg-surface-elevated border border-border p-2 space-y-1.5 font-mono text-[9px] flex-shrink-0 mt-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 truncate">
            <span className="w-1.5 h-1.5 rounded-full bg-success flex-shrink-0" />
            {!isCollapsed && (
              <span className="font-semibold text-text tracking-wide truncate">
                AIR-GAPPED
              </span>
            )}
          </div>
          {!isCollapsed && (
            <span className="text-text-tertiary">{AGENTS.length} AGENTS</span>
          )}
        </div>

        <div className="w-full bg-surface-base rounded-full h-1 overflow-hidden">
          <div
            className="bg-copper h-full transition-all duration-300"
            style={{ width: `${Math.min(100, Math.max(5, telemetry.vramPct))}%` }}
          />
        </div>

        {!isCollapsed && (
          <div className="flex justify-between text-text-tertiary">
            <span>VRAM: {telemetry.vramUsed.toFixed(1)}/{telemetry.vramTotal.toFixed(1)} GB</span>
            <span className="text-success font-medium">OK</span>
          </div>
        )}
      </div>
    </aside>
  );
};
