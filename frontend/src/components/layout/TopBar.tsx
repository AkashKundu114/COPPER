import React, { useState, useEffect } from "react";
import { GitBranch, Search, Volume2, VolumeX } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";
import { CognitiveStatusBadge } from "../ambient/CognitiveStatusBadge";
import { soundFX } from "../../lib/soundFX";
import { systemAPI } from "../../services/api";
import { Badge } from "../ui/Badge";

interface TopBarProps {
  sectionTitle: string;
  profile: ProfileResponse | null;
  drawerOpen: boolean;
  onToggleDrawer: () => void;
  onOpenCommandPalette: () => void;
  onToggleClipboard?: () => void;
  isClipboardOpen?: boolean;
}

const SECTION_TITLES: Record<string, string> = {
  dashboard: "Mission Cockpit",
  companion: "Voice Companion",
  chat: "Pair Programmer",
  agents: "Agent Fleet",
  memory: "Memory Graph",
  benchmarks: "Routing & Benchmarks",
  "self-improvement": "Self-Improvement",
  security: "Security Center",
  today: "Daily Standup",
  tasks: "Sprint Backlog",
  projects: "Workspaces",
  meetings: "Architecture Notes",
  email: "Alerts & Feeds",
  research: "Documentation",
  automations: "Automations",
  activity: "System Activity",
  insights: "Analytics",
  food: "Wellness",
  settings: "Settings",
  campaigns: "Campaign Intelligence",
};

export const TopBar: React.FC<TopBarProps> = ({
  sectionTitle,
  onOpenCommandPalette,
}) => {
  const [timeUtc, setTimeUtc] = useState("");
  const [timeLocal, setTimeLocal] = useState("");
  const [isElectron, setIsElectron] = useState(false);
  const [sfxMuted, setSfxMuted] = useState(() => soundFX.isMuted());
  const [gitStatus, setGitStatus] = useState({ branch: "main", repo: "COPPER" });

  useEffect(() => {
    systemAPI
      .getCockpitStatus()
      .then((res) => {
        if (res.data?.git) {
          setGitStatus({
            branch: res.data.git.branch || "main",
            repo: res.data.git.repo || "COPPER",
          });
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const isRunningInElectron =
      typeof window !== "undefined" &&
      (Boolean((window as any).copperAPI) ||
        Boolean((window as any).ipcRenderer) ||
        Boolean((window as any).require) ||
        (typeof navigator !== "undefined" &&
          navigator.userAgent.toLowerCase().includes("electron")));
    setIsElectron(isRunningInElectron);

    const updateTime = () => {
      const now = new Date();
      setTimeUtc(now.toISOString().slice(11, 19) + "Z");
      setTimeLocal(now.toLocaleTimeString([], { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const displayTitle =
    SECTION_TITLES[sectionTitle] || sectionTitle.replace(/-/g, " ");

  return (
    <header
      role="banner"
      aria-label="Top Bar Controls and Status"
      className="drag-region h-11 bg-surface-base/90 backdrop-blur-sm border-b border-border flex items-center justify-between px-3 md:px-4 z-20 select-none flex-shrink-0"
    >
      {/* Left: Section Title & Repository context */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-copper" aria-hidden="true" />
          <h2 className="font-sans text-xs font-semibold text-text uppercase tracking-wider whitespace-nowrap">
            {displayTitle}
          </h2>
        </div>

        <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-surface-elevated border border-border-subtle font-mono text-[10px] text-text-secondary">
          <GitBranch size={11} className="text-copper" />
          <span className="text-text font-medium">{gitStatus.branch}</span>
          <span className="text-text-tertiary">/</span>
          <span className="text-text-secondary">{gitStatus.repo}</span>
          <span className="text-text-tertiary">·</span>
          <Badge variant="success">AIR-GAP</Badge>
        </div>
      </div>

      {/* Center: Command Palette Trigger */}
      <div className="flex items-center justify-center flex-1 max-w-xs md:max-w-sm px-2">
        <button
          onClick={() => {
            soundFX.play("click");
            onOpenCommandPalette();
          }}
          aria-label="Open command palette (Ctrl+K)"
          className="no-drag w-full flex items-center justify-between gap-2 px-2.5 py-1 rounded-md bg-surface-elevated hover:bg-surface-hover border border-border-subtle hover:border-border text-xs text-text-secondary hover:text-text transition-colors group cursor-pointer"
        >
          <div className="flex items-center gap-1.5 overflow-hidden">
            <Search size={12} className="text-copper flex-shrink-0" aria-hidden="true" />
            <span className="text-[11px] tracking-tight truncate">Search or jump to...</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded bg-surface-base text-[9px] font-mono text-text-tertiary border border-border-subtle font-medium">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right: Telemetry & Actions */}
      <div className={`flex items-center gap-2 flex-shrink-0 ${isElectron ? "pr-36" : "pr-1 sm:pr-2"}`}>
        {/* Local Clock */}
        <div
          className="hidden lg:flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-surface-elevated border border-border-subtle font-mono text-[10px] whitespace-nowrap cursor-default"
          title={`Local: ${timeLocal} | UTC: ${timeUtc}`}
          aria-label={`Local time: ${timeLocal}, UTC time: ${timeUtc}`}
        >
          <span className="text-text-tertiary">LOC</span>
          <span className="text-copper font-medium">{timeLocal}</span>
        </div>

        {/* Real-Time Ambient Cognitive Load */}
        <CognitiveStatusBadge />

        {/* Audio SFX Toggle */}
        <button
          onClick={() => {
            const next = soundFX.toggleMute();
            setSfxMuted(next);
          }}
          className="no-drag p-1 rounded-md text-text-secondary hover:text-text hover:bg-surface-hover transition-colors cursor-pointer"
          title={sfxMuted ? "Unmute UI Sound Effects" : "Mute UI Sound Effects"}
          aria-label={sfxMuted ? "Unmute UI Sound Effects" : "Mute UI Sound Effects"}
        >
          {sfxMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
        </button>
      </div>
    </header>
  );
};
