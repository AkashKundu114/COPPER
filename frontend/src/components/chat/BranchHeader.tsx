import React, { useState } from "react";
import {
  GitBranch,
  GitCompare,
  GitMerge,
  ChevronDown,
  Check,
  GitGraph,
} from "lucide-react";
import { type BranchItem } from "../../services/api";
import { BranchGraph } from "./BranchGraph";

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
  const [showGraph, setShowGraph] = useState(false);
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
    <div className="w-full max-w-[850px] flex flex-col z-20">
      <div className="px-4 py-2 flex items-center justify-between border-b border-border-subtle bg-canvas/70 backdrop-blur text-xs font-mono select-none">
        {/* Branch Selector Dropdown */}
        <div className="relative">
          <button
            ref={triggerButtonRef}
            onClick={() => setDropdownOpen(!dropdownOpen)}
            aria-haspopup="listbox"
            aria-expanded={dropdownOpen}
            aria-controls="branch-listbox"
            aria-label={`Conversation branch: ${activeBranch.title}`}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-hover border border-border-subtle text-text transition-all font-sans font-bold text-xs cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
          >
            <GitBranch size={14} className={isMain ? "text-accent-400" : "text-amber-400"} aria-hidden="true" />
            <span className="truncate max-w-[200px] md:max-w-[320px]">
              {activeBranch.title}
            </span>
            <span className="px-1.5 py-0.2 rounded bg-surface-active text-[10px] text-text-secondary font-mono">
              {activeBranch.messages_count ?? 0}
            </span>
            <ChevronDown size={12} className={`text-text-secondary transition-transform ${dropdownOpen ? "rotate-180" : ""}`} aria-hidden="true" />
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-30" onClick={() => setDropdownOpen(false)} aria-hidden="true" />
              <div
                role="listbox"
                id="branch-listbox"
                aria-label="Available conversation branches"
                className="absolute left-0 mt-1.5 w-72 rounded-xl bg-canvas border border-border-subtle shadow-2xl p-1.5 z-40 space-y-1"
              >
                <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-text-secondary tracking-wider">
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
                            : "text-text-secondary hover:bg-surface-elevated"
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
                        <div className="flex items-center gap-1.5 shrink-0 text-[10px] font-mono text-text-secondary">
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
            onClick={() => setShowGraph(!showGraph)}
            aria-label="Toggle branch graph visualization"
            className={`flex items-center justify-center p-1.5 rounded-lg border text-[11px] font-bold transition-all cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan ${
              showGraph 
                ? "bg-accent-950 text-accent-400 border-accent-800/50" 
                : "bg-surface-elevated hover:bg-surface-hover text-text-secondary border-border-subtle"
            }`}
            title="Toggle Branch Graph"
          >
            <GitGraph size={14} aria-hidden="true" />
          </button>
          
          <button
            onClick={onOpenCompare}
            disabled={branches.length < 2}
            aria-label="Compare divergent conversation branches"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-elevated hover:bg-surface-hover text-text-secondary border border-border-subtle text-[11px] font-bold transition-all disabled:opacity-40 disabled:pointer-events-none cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
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
      
      {/* Branch Graph Visualization Panel */}
      {showGraph && (
        <div className="w-full border-b border-border-subtle shadow-inner">
          <BranchGraph
            branches={branches}
            activeBranchId={activeBranchId}
            onSelectBranch={onSelectBranch}
          />
        </div>
      )}
    </div>
  );
};
