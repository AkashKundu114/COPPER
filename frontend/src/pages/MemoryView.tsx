import React, { useState, useEffect } from "react";
import { Plus, Trash2, Search, X, Network, Brain } from "lucide-react";
import { memoryCRUDAPI, knowledgeAPI, type EpistemicMemoryItem } from "../lib/api";
import { KnowledgeGraphView } from "../components/knowledge/KnowledgeGraphView";
import { CausalExplorerTab } from "../components/memory/CausalExplorerTab";
import { MemoryProvenanceTab } from "../components/memory/MemoryProvenanceTab";

const DEFAULT_SDE_MEMORIES: EpistemicMemoryItem[] = [
  {
    id: "mem-1",
    category: "Architecture",
    type: "fact",
    content: "C.O.P.P.E.R. operates with 30 local GGUF/ONNX models with 100% offline air-gapped zero egress.",
    confidence: 0.99,
    evidenceCount: 14,
    lastConfirmed: "Just now",
  },
  {
    id: "mem-2",
    category: "Inference Engine",
    type: "fact",
    content: "TFP-Router achieves sub-millisecond (0.105ms) intent classification across 1,390 benchmark tests (~9,856 QPS).",
    confidence: 0.98,
    evidenceCount: 22,
    lastConfirmed: "Just now",
  },
  {
    id: "mem-3",
    category: "Developer Toolchain",
    type: "observation",
    content: "User primarily codes in TypeScript/React 19 on frontend and Python 3.11+ on local backend.",
    confidence: 0.82,
    evidenceCount: 9,
    lastConfirmed: "1h ago",
  },
  {
    id: "mem-4",
    category: "Performance Optimization",
    type: "hypothesis",
    content: "Offloading Whisper Large v3 Turbo audio inference to GPU tensor cores reduces latency by ~42%.",
    confidence: 0.45,
    evidenceCount: 3,
    lastConfirmed: "1d ago",
  },
];

export const MemoryView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"graph" | "epistemic" | "causal" | "provenance">("graph");
  const [memories, setMemories] = useState<EpistemicMemoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState("");
  const [activeType, setActiveType] = useState<
    "all" | "fact" | "observation" | "hypothesis"
  >("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [category, setCategory] = useState("User Preference");
  const [type, setType] = useState<EpistemicMemoryItem["type"]>("fact");
  const [content, setContent] = useState("");
  const [confidence, setConfidence] = useState(95);
  const [syncingGraph, setSyncingGraph] = useState(false);

  const handleSyncMemoriesToGraph = async () => {
    setSyncingGraph(true);
    try {
      await knowledgeAPI.syncMemories();
    } catch (err) {
      console.error("Failed to sync memories to graph:", err);
    } finally {
      setSyncingGraph(false);
    }
  };

  const loadMemories = async () => {
    try {
      const data = await memoryCRUDAPI.list();
      if (data && data.length > 0) {
        setMemories(data);
      } else {
        setMemories(DEFAULT_SDE_MEMORIES);
      }
    } catch (err) {
      console.error("Failed to load epistemic memories from backend, using defaults:", err);
      setMemories(DEFAULT_SDE_MEMORIES);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    const payload = {
      type,
      category: category.trim() || "General",
      content: content.trim(),
      confidence: confidence / 100,
      evidenceCount: 1,
    };

    try {
      const newMemory = await memoryCRUDAPI.create(payload);
      setMemories((prev) => [newMemory, ...prev]);
      setContent("");
      setIsModalOpen(false);
    } catch (err) {
      console.error("Failed to create epistemic memory:", err);
    }
  };

  const handleForget = async (id: string) => {
    try {
      await memoryCRUDAPI.delete(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error("Failed to delete epistemic memory:", err);
    }
  };

  const filtered = memories.filter((m) => {
    const matchesSearch =
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = activeType === "all" || m.type === activeType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="modern-page flex flex-col h-full w-full overflow-hidden text-slate-200 select-none font-mono text-xs">
      {/* View Switcher Header Tab Bar */}
      <div className="px-6 pt-4 pb-2 border-b border-cyber-cyan/15 bg-black/60 backdrop-blur-xl flex items-center justify-between">
        <div className="flex items-center gap-1 p-1 bg-[#1A0A0F]/80 rounded-xl border border-blush-100/[0.10]">
          <button
            onClick={() => setActiveTab("graph")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "graph"
                ? "bg-blush-100 text-burgundy-950 shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Network size={14} />
            <span>Knowledge Graph</span>
          </button>
          <button
            onClick={() => setActiveTab("epistemic")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "epistemic"
                ? "bg-blush-100 text-burgundy-950 shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Brain size={14} />
            <span>Memories ({memories.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("causal")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "causal"
                ? "bg-blush-100 text-burgundy-950 shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Network size={14} />
            <span>Causal Explorer</span>
          </button>
          <button
            onClick={() => setActiveTab("provenance")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "provenance"
                ? "bg-blush-100 text-burgundy-950 shadow-sm"
                : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
            }`}
          >
            <Brain size={14} />
            <span>Provenance Audit</span>
          </button>
        </div>

        {activeTab === "epistemic" && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleSyncMemoriesToGraph}
              disabled={syncingGraph}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyber-cyan/15 hover:bg-cyber-cyan/25 text-cyber-cyan border border-cyber-cyan/40 font-bold text-xs transition-all shadow-sm cursor-pointer disabled:opacity-50"
              title="Sync active memories into knowledge graph"
            >
              <Network size={14} />
              <span>{syncingGraph ? "Syncing..." : "Sync to Graph"}</span>
            </button>
            <button
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blush-100 hover:bg-white text-burgundy-950 font-bold text-xs transition-all shadow-sm cursor-pointer"
            >
              <Plus size={15} strokeWidth={2.5} />
              <span>Add Memory Fact</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {activeTab === "graph" ? (
        <div className="flex-1 w-full overflow-hidden">
          <KnowledgeGraphView />
        </div>
      ) : activeTab === "causal" ? (
        <CausalExplorerTab />
      ) : activeTab === "provenance" ? (
        <MemoryProvenanceTab />
      ) : (
        <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto w-full custom-scrollbar">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight font-sans">
                Epistemic Memory Center
              </h1>
              <p className="text-xs text-slate-400">
                Facts (Confidence ≥ 85%), Observations (50% to 85%), and Hypotheses (10% to 50%)
              </p>
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <Search size={14} className="absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                placeholder="Search learned memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white outline-none focus:border-accent-500"
              />
            </div>
            <div className="flex gap-1.5 p-1 bg-slate-900 rounded-xl border border-slate-800 w-full sm:w-auto">
              {(["all", "fact", "observation", "hypothesis"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveType(t)}
                  className={`px-3 py-1.5 rounded-lg capitalize transition-all ${
                    activeType === t
                      ? "bg-accent-500/20 text-accent-400 border border-accent-500/40"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {t} ({t === "all" ? memories.length : memories.filter((m) => m.type === t).length})
                </button>
              ))}
            </div>
          </div>

          {/* Memory Items */}
          <div className="space-y-3">
            {loading ? (
              <div className="p-12 text-center text-slate-500 bg-slate-900/60 rounded-2xl border border-slate-800">
                Loading memories...
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-12 text-center text-slate-500 bg-slate-900/60 rounded-2xl border border-slate-800">
                No memories match your query.
              </div>
            ) : (
              filtered.map((mem) => (
                <div
                  key={mem.id}
                  className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2 hover:border-slate-700 transition-all shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2.5 py-0.5 rounded-full font-bold uppercase text-[10px] ${
                          mem.type === "fact"
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800/40"
                            : mem.type === "observation"
                              ? "bg-blue-950 text-blue-400 border border-blue-800/40"
                              : "bg-amber-950 text-amber-400 border border-amber-800/40"
                        }`}
                      >
                        {mem.type}
                      </span>
                      <span className="text-slate-400 font-semibold">{mem.category}</span>
                    </div>
                    <span className="text-[10px] text-slate-500">Last confirmed: {mem.lastConfirmed}</span>
                  </div>

                  <p className="text-xs text-white leading-relaxed font-sans">{mem.content}</p>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px]">
                    <div className="flex gap-4 text-slate-400">
                      <span>
                        Confidence: <strong className="text-white">{Math.round(mem.confidence * 100)}%</strong>
                      </span>
                      <span>
                        Evidence: <strong className="text-white">{mem.evidenceCount}x</strong>
                      </span>
                    </div>
                    <button
                      onClick={() => handleForget(mem.id)}
                      className="flex items-center gap-1 text-slate-500 hover:text-red-400 transition-colors p-1"
                      title="Forget this memory"
                    >
                      <Trash2 size={13} />
                      <span>Forget</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Add Memory Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Add Memory Rule / Fact</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleAddMemory} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Category</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Coding Standard, Food Preference..."
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Memory Content / Statement</label>
                <textarea
                  required
                  placeholder="e.g. Always generate concise Python code with type annotations."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500 resize-none h-20 font-sans text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Memory Type</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="fact">Fact (≥ 85%)</option>
                    <option value="observation">Observation (50-85%)</option>
                    <option value="hypothesis">Hypothesis (&lt; 50%)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Confidence ({confidence}%)</label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    value={confidence}
                    onChange={(e) => setConfidence(Number(e.target.value))}
                    className="w-full mt-2 accent-accent-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl hover:bg-slate-800 text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold shadow-md"
                >
                  Save Fact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
