import { Sparkles, PanelRightOpen, PanelRightClose } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";

interface Props {
  profile: ProfileResponse | null;
  drawerOpen: boolean;
  onToggleDrawer: () => void;
}

export function TopBar({ profile, drawerOpen, onToggleDrawer }: Props) {
  return (
    <header className="fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-6 py-4 pointer-events-none">
      <div className="flex items-center gap-2 pointer-events-auto">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-copper-hot to-copper-base flex items-center justify-center">
          <Sparkles size={14} className="text-void" />
        </div>
        <span className="font-display font-semibold tracking-wide text-ink-primary">COPPER</span>
      </div>

      <div className="flex items-center gap-3 pointer-events-auto">
        {profile && (
          <span className="font-mono text-[11px] tracking-wide text-copper-flare border border-copper-dim/50 rounded-full px-3 py-1 bg-void-panel/70 backdrop-blur-md">
            {profile.relationship_tier}
          </span>
        )}
        <button
          onClick={onToggleDrawer}
          className="text-ink-secondary hover:text-ink-primary transition-colors"
          aria-label="Toggle memory panel"
        >
          {drawerOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
        </button>
      </div>
    </header>
  );
}
