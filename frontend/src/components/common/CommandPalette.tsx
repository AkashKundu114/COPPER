import React, { useEffect, useState } from "react";
import { Search, Brain, Shield, Calendar, Bot, CheckSquare, Settings } from "lucide-react";
import type { NavSection } from "../layout/Sidebar";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onSelectSection: (section: NavSection) => void;
}

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

  const commands = [
    { label: "Ask COPPER Assistant", section: "chat" as NavSection, icon: Brain },
    { label: "Open Schedule & Today View", section: "today" as NavSection, icon: Calendar },
    { label: "Create / View Tasks", section: "tasks" as NavSection, icon: CheckSquare },
    { label: "Open Memory Center", section: "memory" as NavSection, icon: Brain },
    { label: "Manage Agent Registry", section: "agents" as NavSection, icon: Bot },
    { label: "Open Security Center", section: "security" as NavSection, icon: Shield },
    { label: "Settings & Developer Mode", section: "settings" as NavSection, icon: Settings },
  ].filter((c) => c.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-start justify-center pt-24 select-none">
      <div className="w-full max-w-xl bg-[#0d0d11] border border-[#b87333]/40 rounded-xl shadow-2xl overflow-hidden">
        {/* Input Header */}
        <div className="flex items-center px-4 py-3 border-b border-white/10 gap-3">
          <Search size={18} className="text-[#ff5722]" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search section..."
            autoFocus
            className="w-full bg-transparent border-none outline-none text-white text-sm placeholder-gray-500 font-mono"
          />
          <kbd className="px-2 py-0.5 rounded bg-white/5 text-[10px] text-gray-400 border border-white/10 font-mono">
            ESC
          </kbd>
        </div>

        {/* Command List */}
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
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs text-gray-300 hover:bg-[#b87333]/20 hover:text-white transition-all text-left group"
                >
                  <div className="flex items-center gap-3">
                    <Icon size={16} className="text-gray-400 group-hover:text-[#ff5722]" />
                    <span>{cmd.label}</span>
                  </div>
                  <span className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">
                    {cmd.section}
                  </span>
                </button>
              );
            })
          ) : (
            <div className="p-4 text-center text-xs text-gray-500 font-mono">
              No matching commands found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
