import React from "react";
import { Shield, Server, Search, User } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";

interface TopBarProps {
  sectionTitle: string;
  profile: ProfileResponse | null;
  drawerOpen: boolean;
  onToggleDrawer: () => void;
  onOpenCommandPalette: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  sectionTitle,
  profile,
  onToggleDrawer,
  onOpenCommandPalette,
}) => {
  return (
    <header className="drag-region h-14 bg-bg border-b border-neon flex items-center justify-between px-6 z-20 select-none shadow-hud">
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-medium text-accent tracking-tight capitalize glow-text">
          {sectionTitle}
        </h2>
      </div>

      <button
        onClick={onOpenCommandPalette}
        className="no-drag flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-panel border border-border text-[13px] text-text-muted hover:text-text hover:border-accent hover:shadow-neon transition-all w-64 justify-between"
      >
        <div className="flex items-center gap-2">
          <Search size={14} className="text-accent" />
          <span>Search or command...</span>
        </div>
        <kbd className="px-1.5 py-0.5 rounded bg-bg text-[10px] font-mono text-text-muted border border-border">
          Ctrl+K
        </kbd>
      </button>

      <div className="flex items-center gap-3 pr-36">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-bg-panel border border-border text-text-muted text-[11px] font-medium">
          <Server size={12} />
          <span>Local</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-bg-panel border border-border text-text-muted text-[11px] font-medium">
          <Shield size={12} />
          <span>Private</span>
        </div>

        <button
          onClick={onToggleDrawer}
          className="no-drag flex items-center gap-2 px-3 py-1 rounded-lg bg-bg-panel border border-border hover:border-accent hover:shadow-neon text-[13px] text-text-muted transition-all"
        >
          <User size={14} />
          <span className="font-medium">
            {profile?.relationship_tier || "Profile"}
          </span>
        </button>
      </div>
    </header>
  );
};
