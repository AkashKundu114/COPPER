import React, { useState, useEffect } from "react";
import { Plus, Trash2, Search, X, Network, Brain } from "lucide-react";
import { workspaceAPI } from "../lib/api";
import { KnowledgeGraphView } from "../components/knowledge/KnowledgeGraphView";

export interface EpistemicMemoryItem {
  id: string;
  type: "fact" | "observation" | "hypothesis";
  category: string;
  content: string;
  confidence: number;
  evidenceCount: number;
  lastConfirmed: string;
}

export const MemoryView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"graph" | "epistemic">("graph");
  const [memories, setMemories] = useState<EpistemicMemoryItem[]>([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [activeType, setActiveType] = useState<
    "all" | "fact" | "observation" | "hypothesis"
  >("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [category, setCategory] = useState("User Preference");
  const [type, setType] = useState<EpistemicMemoryItem["type"]>("fact");
  const [content, setContent] = useState("");
  const [confidence, setConfidence] = useState(95);

  useEffect(() => {
    workspaceAPI.list<EpistemicMemoryItem>("memory").then(setMemories).catch(console.error);
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
      lastConfirmed: "Just now",
    };

    const newMemory = await workspaceAPI.create<EpistemicMemoryItem>("memory", payload);
    setMemories((prev) => [newMemory, ...prev]);
    setContent("");
    setIsModalOpen(false);
  };

  const handleForget = async (id: string) => {
    await workspaceAPI.remove("memory", id);
    setMemories((prev) => prev.filter((m) => m.id !== id));
  };

  const filtered = memories.filter((m) => {
    const matchesSearch =
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = activeType === "all" || m.type === activeType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="flex flex-col h-full w-full overflow-hidden text-slate-200 select-none font-mono text-xs">
      {/* View Switcher Header Tab Bar */}
      <div className="px-6 pt-4 pb-2 border-b border-cyber-cyan/15 bg-black/60 backdrop-blur-xl flex items-center justify-between">
        <div className="flex items-center gap-2 p-1 bg-black/80 rounded-xl border border-zinc-800">
          <button
            onClick={() => setActiveTab("graph")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "graph"
                ? "bg-cyber-cyan text-black shadow-[0_0_15px_rgba(0,240,255,0.4)]"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Network size={14} />
            <span>Neural Knowledge Graph (ATLAS)</span>
          </button>
          <button
            onClick={() => setActiveTab("epistemic")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "epistemic"
                ? "bg-accent-500 text-black shadow-[0_0_15px_rgba(245,158,11,0.4)]"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <Brain size={14} />
            <span>Epistemic Memories ({memories.length})</span>
          </button>
        </div>

        {activeTab === "epistemic" && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
          >
            <Plus size={15} strokeWidth={2.5} />
            <span>Add Memory Fact</span>
          </button>
        )}
      </div>

      {/* Main Content Area */}
      {activeTab === "graph" ? (
        <div className="flex-1 w-full overflow-hidden">
          <KnowledgeGraphView />
        </div>
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
            {filtered.length === 0 ? (
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
