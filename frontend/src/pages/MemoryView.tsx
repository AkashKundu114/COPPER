import React, { useState, useEffect } from "react";
import { Plus, Trash2, Search, X } from "lucide-react";

export interface EpistemicMemoryItem {
  id: string;
  type: "fact" | "observation" | "hypothesis";
  category: string;
  content: string;
  confidence: number;
  evidenceCount: number;
  lastConfirmed: string;
}

const STORAGE_KEY = "copper_memories_data";

const DEFAULT_MEMORIES: EpistemicMemoryItem[] = [
  {
    id: "m1",
    type: "fact",
    category: "Hardware Specs",
    content:
      "Windows 11 with NVIDIA RTX 5060 Laptop GPU (8GB VRAM) and AMD Ryzen 9 8940HX.",
    confidence: 0.99,
    evidenceCount: 30,
    lastConfirmed: "Today",
  },
  {
    id: "m2",
    type: "fact",
    category: "Privacy Constraint",
    content:
      "Default to 100% offline local model execution via Ollama. No remote telemetry.",
    confidence: 1.0,
    evidenceCount: 45,
    lastConfirmed: "Today",
  },
  {
    id: "m3",
    type: "observation",
    category: "Working Habit",
    content:
      "User works on full-stack TypeScript, React, and Python AI architectures.",
    confidence: 0.92,
    evidenceCount: 18,
    lastConfirmed: "Today",
  },
  {
    id: "m4",
    type: "hypothesis",
    category: "UI Preference",
    content:
      "User prefers dark glassmorphism cyber-HUD with rich formatted typography and timestamps.",
    confidence: 0.88,
    evidenceCount: 12,
    lastConfirmed: "Today",
  },
];

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<EpistemicMemoryItem[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : DEFAULT_MEMORIES;
    } catch {
      return DEFAULT_MEMORIES;
    }
  });

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
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(memories));
    } catch (e) {
      console.error(e);
    }
  }, [memories]);

  const handleAddMemory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    const newMemory: EpistemicMemoryItem = {
      id: `mem-${Date.now()}`,
      type,
      category: category.trim() || "General",
      content: content.trim(),
      confidence: confidence / 100,
      evidenceCount: 1,
      lastConfirmed: "Just now",
    };

    setMemories((prev) => [newMemory, ...prev]);
    setContent("");
    setIsModalOpen(false);
  };

  const handleForget = (id: string) => {
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
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">
            Epistemic Memory Center
          </h1>
          <p className="text-xs text-slate-400">
            Facts (Confidence ≥ 85%), Observations (50% to 85%), and Hypotheses
            (10% to 50%)
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
        >
          <Plus size={15} strokeWidth={2.5} />
          <span>Add Memory Fact</span>
        </button>
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
              {t} (
              {t === "all"
                ? memories.length
                : memories.filter((m) => m.type === t).length}
              )
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
                        ? "bg-verdigris-950 text-verdigris-400 border border-verdigris-800/40"
                        : mem.type === "observation"
                          ? "bg-blue-950 text-blue-400 border border-blue-800/40"
                          : "bg-molten-950 text-molten-400 border border-molten-800/40"
                    }`}
                  >
                    {mem.type}
                  </span>
                  <span className="text-slate-400 font-semibold">
                    {mem.category}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500">
                  Last confirmed: {mem.lastConfirmed}
                </span>
              </div>

              <p className="text-xs text-white leading-relaxed font-sans">
                {mem.content}
              </p>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px]">
                <div className="flex gap-4 text-slate-400">
                  <span>
                    Confidence:{" "}
                    <strong className="text-white">
                      {Math.round(mem.confidence * 100)}%
                    </strong>
                  </span>
                  <span>
                    Evidence:{" "}
                    <strong className="text-white">{mem.evidenceCount}x</strong>
                  </span>
                </div>
                <button
                  onClick={() => handleForget(mem.id)}
                  className="flex items-center gap-1 text-slate-500 hover:text-danger-400 transition-colors p-1"
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

      {/* Add Memory Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">
                Add Memory Rule / Fact
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleAddMemory} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Category
                </label>
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
                <label className="text-[11px] text-slate-400 block mb-1">
                  Memory Content / Statement
                </label>
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
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Memory Type
                  </label>
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
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Confidence ({confidence}%)
                  </label>
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
