import React from "react";
import { Mic, Shield, Server, Search, User } from "lucide-react";
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
    <header className="h-14 bg-[#0d0d11]/80 backdrop-blur-md border-b border-[#b87333]/20 flex items-center justify-between px-6 z-20 select-none">
      {/* Left: Section Title */}
      <div className="flex items-center gap-3">
        <h2 className="text-sm font-semibold text-white tracking-wide capitalize">{sectionTitle}</h2>
      </div>

      {/* Center: Command Palette Trigger */}
      <button
        onClick={onOpenCommandPalette}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14141a] border border-white/10 text-xs text-gray-400 hover:text-gray-200 hover:border-white/20 transition-all w-64 justify-between"
      >
        <div className="flex items-center gap-2">
          <Search size={14} className="text-gray-400" />
          <span>Search or command...</span>
        </div>
        <kbd className="px-1.5 py-0.5 rounded bg-black/40 text-[10px] font-mono text-gray-500 border border-white/5">
          Ctrl+K
        </kbd>
      </button>

      {/* Right: Status Badges & Profile */}
      <div className="flex items-center gap-3">
        {/* Status Badge 1: Local Model */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <Server size={12} />
          <span>● Local</span>
        </div>

        {/* Status Badge 2: Privacy */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-950/40 border border-blue-500/30 text-blue-400 text-xs font-mono">
          <Shield size={12} />
          <span>🔒 Private</span>
        </div>

        {/* Status Badge 3: Voice Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#b87333]/20 border border-[#b87333]/40 text-[#ff5722] text-xs font-mono">
          <Mic size={12} />
          <span>🎙 Ready</span>
        </div>

        {/* Profile / Tier Button */}
        <button
          onClick={onToggleDrawer}
          className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#14141a] border border-[#b87333]/30 hover:border-[#ff5722]/60 text-xs text-gray-200 transition-all"
        >
          <User size={14} className="text-[#ff5722]" />
          <span className="font-mono text-[11px]">{profile?.relationship_tier || "User Profile"}</span>
        </button>
      </div>
    </header>
  );
};
