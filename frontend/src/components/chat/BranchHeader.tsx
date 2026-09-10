import React, { useState } from "react";
import {
  GitBranch,
  GitCompare,
  GitMerge,
  ChevronDown,
  Check,
} from "lucide-react";
import { type BranchItem } from "../../services/api";

interface Props {
  branches: BranchItem[];
  activeBranchId: string;
  onSelectBranch: (branchId: string) => void;
  onOpenCompare: () => void;
  onMergeBranch?: (branchId: string) => void;
}

export const BranchHeader: React.FC<Props> = ({
  branches,
  activeBranchId,
  onSelectBranch,
  onOpenCompare,
  onMergeBranch,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const triggerButtonRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (!dropdownOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setDropdownOpen(false);
        triggerButtonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [dropdownOpen]);

  const activeBranch = branches.find((b) => b.branch_id === activeBranchId) || {
    branch_id: activeBranchId,
    title: "Main Timeline",
    is_main: true,
    messages_count: 0,
  };

  const isMain = activeBranch.is_main || activeBranchId === "default" || !activeBranch.parent_session_id;

  return (
    <div className="w-full max-w-[850px] px-4 py-2 flex items-center justify-between border-b border-slate-800/80 bg-slate-950/70 backdrop-blur text-xs font-mono select-none z-20">
      {/* Branch Selector Dropdown */}
      <div className="relative">
        <button
          ref={triggerButtonRef}
          onClick={() => setDropdownOpen(!dropdownOpen)}
          aria-haspopup="listbox"
          aria-expanded={dropdownOpen}
          aria-controls="branch-listbox"
          aria-label={`Conversation branch: ${activeBranch.title}`}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-slate-200 transition-all font-sans font-bold text-xs cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
        >
          <GitBranch size={14} className={isMain ? "text-accent-400" : "text-amber-400"} aria-hidden="true" />
          <span className="truncate max-w-[200px] md:max-w-[320px]">
            {activeBranch.title}
          </span>
          <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-slate-400 font-mono">
            {activeBranch.messages_count ?? 0}
          </span>
          <ChevronDown size={12} className={`text-slate-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} aria-hidden="true" />
        </button>

        {dropdownOpen && (
          <>
            <div className="fixed inset-0 z-30" onClick={() => setDropdownOpen(false)} aria-hidden="true" />
            <div
              role="listbox"
              id="branch-listbox"
              aria-label="Available conversation branches"
              className="absolute left-0 mt-1.5 w-72 rounded-xl bg-slate-950 border border-slate-800 shadow-2xl p-1.5 z-40 space-y-1"
            >
              <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                Conversation Branches ({branches.length})
              </div>

              <div className="max-h-56 overflow-y-auto space-y-1 custom-scrollbar">
                {branches.map((b) => {
                  const isSelected = b.branch_id === activeBranchId;
                  return (
                    <button
                      key={b.branch_id}
                      role="option"
                      aria-selected={isSelected}
                      aria-label={`${b.title}${b.is_main ? " (Main branch)" : ""}, ${b.messages_count ?? 0} messages`}
                      onClick={() => {
                        onSelectBranch(b.branch_id);
                        setDropdownOpen(false);
                        triggerButtonRef.current?.focus();
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left transition-colors text-[11px] cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan ${
                        isSelected
                          ? "bg-accent-950 text-white border border-accent-800/50"
                          : "text-slate-300 hover:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate pr-2">
                        <GitBranch
                          size={12}
                          className={b.is_main ? "text-accent-400 shrink-0" : "text-amber-400 shrink-0"}
                          aria-hidden="true"
                        />
                        <span className="truncate font-sans font-medium">{b.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0 text-[10px] font-mono text-slate-400">
                        <span>{b.messages_count ?? "?"}</span>
                        {isSelected && <Check size={12} className="text-accent-400" aria-hidden="true" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenCompare}
          disabled={branches.length < 2}
          aria-label="Compare divergent conversation branches"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 text-slate-300 border border-slate-800 text-[11px] font-bold transition-all disabled:opacity-40 disabled:pointer-events-none cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
          title="Compare divergent conversation branches"
        >
          <GitCompare size={13} className="text-accent-400" aria-hidden="true" />
          <span className="hidden sm:inline">Compare</span>
        </button>

        {!isMain && onMergeBranch && (
          <button
            onClick={() => onMergeBranch(activeBranchId)}
            aria-label="Merge branch discoveries back into main timeline"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-verdigris-950 hover:bg-verdigris-900 text-verdigris-300 border border-verdigris-800/50 text-[11px] font-bold transition-all cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
            title="Merge branch discoveries back into main timeline"
          >
            <GitMerge size={13} className="text-verdigris-400" aria-hidden="true" />
            <span className="hidden sm:inline">Merge Main</span>
          </button>
        )}
      </div>
    </div>
  );
};
