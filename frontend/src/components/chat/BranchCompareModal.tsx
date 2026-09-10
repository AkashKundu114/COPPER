import React, { useEffect, useState } from "react";
import {
  GitBranch,
  GitMerge,
  GitCompare,
  X,
  RefreshCw,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Award,
} from "lucide-react";
import { branchingAPI, type BranchItem, type DiffComparison } from "../../services/api";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  branches: BranchItem[];
  currentBranchId: string;
  onMerged?: (targetSessionId: string) => void;
}

export const BranchCompareModal: React.FC<Props> = ({
  isOpen,
  onClose,
  branches,
  currentBranchId,
  onMerged,
}) => {
  const [branchAId, setBranchAId] = useState<string>("");
  const [branchBId, setBranchBId] = useState<string>("");
  const [diff, setDiff] = useState<DiffComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMerging, setIsMerging] = useState(false);
  const [bannerMessage, setBannerMessage] = useState<string | null>(null);

  // Initialize selected branches
  useEffect(() => {
    if (branches.length >= 2) {
      setBranchAId(branches[0].branch_id);
      setBranchBId(branches[1].branch_id);
    } else if (branches.length === 1) {
      setBranchAId(branches[0].branch_id);
      setBranchBId(branches[0].branch_id);
    }
  }, [branches, isOpen]);

  // Load comparison whenever selection changes
  const runComparison = async () => {
    if (!branchAId || !branchBId) return;
    setIsLoading(true);
    setBannerMessage(null);
    try {
      const res = await branchingAPI.compareBranches(branchAId, branchBId);
      if (res.status === "success" && res.comparison) {
        setDiff(res.comparison);
      }
    } catch (err: any) {
      console.error("Comparison error:", err);
      setBannerMessage(`Diff failed: ${err.message || "Failed to compare branches"}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && branchAId && branchBId) {
      runComparison();
    }
  }, [isOpen, branchAId, branchBId]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleMergeBranch = async (sourceBranchId: string) => {
    setIsMerging(true);
    try {
      const targetId = branches.find((b) => b.is_main)?.branch_id || "default";
      const res = await branchingAPI.mergeBranch(sourceBranchId, targetId);
      if (res.success) {
        setBannerMessage(`Merged insights into '${targetId}'!`);
        if (onMerged) onMerged(targetId);
      }
    } catch (err: any) {
      setBannerMessage(`Merge failed: ${err.message}`);
    } finally {
      setIsMerging(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="branch-compare-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in font-mono text-xs"
    >
      <div className="bg-slate-950 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden text-slate-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-accent-950/80 border border-accent-800/40 text-accent-400" aria-hidden="true">
              <GitCompare size={18} />
            </div>
            <div>
              <h2 id="branch-compare-title" className="text-sm font-bold text-white font-sans flex items-center gap-2">
                Semantic Branch Comparison & Diff
              </h2>
              <p className="text-[10px] text-slate-400">
                Natural language trajectory analysis, key divergence aspects, and mergeable insights
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={runComparison}
              disabled={isLoading}
              aria-label="Refresh branch comparison"
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-all cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
              title="Refresh comparison"
            >
              <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} aria-hidden="true" />
            </button>
            <button
              onClick={onClose}
              aria-label="Close branch comparison dialog"
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-all cursor-pointer focus-visible:ring-1 focus-visible:ring-cyber-cyan"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Branch Selectors Bar */}
        <div className="px-6 py-3 bg-slate-900/40 border-b border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-[10px] text-slate-400 font-bold uppercase whitespace-nowrap">Branch A:</span>
            <select
              value={branchAId}
              aria-label="Select first branch to compare"
              onChange={(e) => setBranchAId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-accent-500 font-mono w-full md:w-60 focus-visible:ring-1 focus-visible:ring-cyber-cyan"
            >
              {branches.map((b) => (
                <option key={b.branch_id} value={b.branch_id}>
                  {b.title} ({b.messages_count ?? "?"} turns)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1 text-slate-500">
            <ArrowRight size={14} />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-[10px] text-slate-400 font-bold uppercase whitespace-nowrap">Branch B:</span>
            <select
              value={branchBId}
              onChange={(e) => setBranchBId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-accent-500 font-mono w-full md:w-60"
            >
              {branches.map((b) => (
                <option key={b.branch_id} value={b.branch_id}>
                  {b.title} ({b.messages_count ?? "?"} turns)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Notifications */}
        {bannerMessage && (
          <div className="mx-6 mt-3 p-3 rounded-xl bg-accent-950/60 border border-accent-500/40 text-accent-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={14} className="text-accent-400 shrink-0" />
              <span>{bannerMessage}</span>
            </div>
            <button onClick={() => setBannerMessage(null)} className="text-[10px] text-slate-400 hover:text-white">
              Dismiss
            </button>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <RefreshCw size={24} className="animate-spin text-accent-400 mx-auto" />
              <p className="text-xs text-slate-400">Analyzing divergent trajectories with DeepSeek-R1...</p>
            </div>
          ) : !diff ? (
            <div className="py-12 text-center text-slate-500 italic">
              Select two branches above to generate semantic diff analysis.
            </div>
          ) : (
            <>
              {/* Divergence Point Banner */}
              <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
                <span className="text-[9px] uppercase font-bold text-slate-500 tracking-wider flex items-center gap-1.5">
                  <GitBranch size={11} className="text-accent-400" />
                  Divergence Point
                </span>
                <p className="text-xs text-slate-200 font-sans leading-relaxed italic">
                  "{diff.divergence_point}"
                </p>
              </div>

              {/* Side-by-Side Summaries */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-accent-400 flex items-center gap-1.5">
                      <GitBranch size={13} />
                      {diff.branch_a_title || "Branch A"}
                    </span>
                    <button
                      onClick={() => handleMergeBranch(branchAId)}
                      disabled={isMerging}
                      className="px-2 py-0.5 rounded bg-accent-950 hover:bg-accent-900 text-accent-300 border border-accent-800/50 text-[10px] font-bold flex items-center gap-1 disabled:opacity-50"
                    >
                      <GitMerge size={11} />
                      <span>Merge A</span>
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed">{diff.branch_a_summary}</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-verdigris-400 flex items-center gap-1.5">
                      <GitBranch size={13} />
                      {diff.branch_b_title || "Branch B"}
                    </span>
                    <button
                      onClick={() => handleMergeBranch(branchBId)}
                      disabled={isMerging}
                      className="px-2 py-0.5 rounded bg-verdigris-950 hover:bg-verdigris-900 text-verdigris-300 border border-verdigris-800/50 text-[10px] font-bold flex items-center gap-1 disabled:opacity-50"
                    >
                      <GitMerge size={11} />
                      <span>Merge B</span>
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-relaxed">{diff.branch_b_summary}</p>
                </div>
              </div>

              {/* Key Differences Table */}
              {diff.key_differences && diff.key_differences.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <span className="text-xs font-bold text-white font-sans flex items-center gap-1.5">
                    <Sparkles size={14} className="text-amber-400" />
                    Key Differences & Divergence Aspects
                  </span>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-500 text-[10px] uppercase">
                          <th className="py-2 px-3 w-1/4">Aspect</th>
                          <th className="py-2 px-3 w-3/8 text-accent-300">Branch A</th>
                          <th className="py-2 px-3 w-3/8 text-verdigris-300">Branch B</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-[11px]">
                        {diff.key_differences.map((diffItem, idx) => (
                          <tr key={idx} className="hover:bg-slate-950/40">
                            <td className="py-2.5 px-3 font-bold text-slate-300">{diffItem.aspect}</td>
                            <td className="py-2.5 px-3 text-slate-400">{diffItem.branch_a}</td>
                            <td className="py-2.5 px-3 text-slate-400">{diffItem.branch_b}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Recommendation & Mergeable Insights */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Recommendation */}
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-white font-sans flex items-center gap-1.5">
                    <Award size={14} className="text-verdigris-400" />
                    Evaluation Recommendation
                  </span>
                  <p className="text-[11px] text-slate-300 leading-relaxed font-sans">{diff.recommendation}</p>
                </div>

                {/* Mergeable Insights */}
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <span className="text-xs font-bold text-white font-sans flex items-center gap-1.5">
                    <GitMerge size={14} className="text-accent-400" />
                    Mergeable Insights
                  </span>
                  {diff.mergeable_insights && diff.mergeable_insights.length > 0 ? (
                    <ul className="space-y-1.5 text-[11px] text-slate-300">
                      {diff.mergeable_insights.map((ins, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-accent-400 font-bold">•</span>
                          <span>{ins}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-slate-500 text-[11px] italic">No unique mergeable insights extracted.</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between">
          <span className="text-[10px] text-slate-500">
            Active Session: <span className="text-slate-300 font-mono">{currentBranchId}</span>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
