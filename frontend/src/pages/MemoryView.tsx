import React, { useState } from "react";
import { Edit2, Trash2 } from "lucide-react";

interface EpistemicMemoryItem {
  id: string;
  type: "fact" | "observation" | "hypothesis";
  category: string;
  content: string;
  confidence: number;
  evidenceCount: number;
  lastConfirmed: string;
}

const MEMORIES: EpistemicMemoryItem[] = [
  { id: "1", type: "fact", category: "System Preference", content: "User operates Windows 11 with RTX 5060 8GB VRAM and Ryzen 9 8940HX.", confidence: 0.98, evidenceCount: 24, lastConfirmed: "Today" },
  { id: "2", type: "fact", category: "Privacy Constraint", content: "User requires 100% offline local model execution via Ollama default.", confidence: 0.99, evidenceCount: 42, lastConfirmed: "Today" },
  { id: "3", type: "observation", category: "Working Habit", content: "User completes deep-work coding sessions most effectively in 60-90 minute focus blocks.", confidence: 0.86, evidenceCount: 14, lastConfirmed: "Yesterday" },
  { id: "4", type: "hypothesis", category: "Productivity Pattern", content: "User prefers dark-mode glassmorphic copper UI over high-contrast light themes.", confidence: 0.45, evidenceCount: 3, lastConfirmed: "3 days ago" },
];

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<EpistemicMemoryItem[]>(MEMORIES);

  const handleForget = (id: string) => {
    setMemories((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Epistemic Memory Center</h1>
        <p className="text-xs text-gray-400 font-mono">Facts (Confidence &ge; 85%), Observations (50% to 85%), and Hypotheses (10% to 50%)</p>
      </div>

      <div className="space-y-3">
        {memories.map((mem) => (
          <div key={mem.id} className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-xs">
                <span
                  className={`px-2 py-0.5 rounded font-bold uppercase ${
                    mem.type === "fact"
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                      : mem.type === "observation"
                      ? "bg-blue-950 text-blue-400 border border-blue-500/30"
                      : "bg-amber-950 text-amber-400 border border-amber-500/30"
                  }`}
                >
                  {mem.type}
                </span>
                <span className="text-gray-400 font-semibold">{mem.category}</span>
              </div>
              <span className="text-[10px] text-gray-500 font-mono">Last confirmed: {mem.lastConfirmed}</span>
            </div>

            <p className="text-xs font-medium text-white leading-relaxed">{mem.content}</p>

            <div className="flex items-center justify-between pt-2 border-t border-white/5 font-mono text-[11px]">
              <div className="flex gap-4 text-gray-400">
                <span>Confidence: <strong className="text-white">{(mem.confidence * 100).toFixed(0)}%</strong></span>
                <span>Evidence: <strong className="text-white">{mem.evidenceCount} instances</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <button className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-gray-300 flex items-center gap-1 border border-white/10">
                  <Edit2 size={10} /> Edit
                </button>
                <button
                  onClick={() => handleForget(mem.id)}
                  className="px-2 py-1 bg-red-950/40 hover:bg-red-900/60 text-red-300 rounded flex items-center gap-1 border border-red-500/30"
                >
                  <Trash2 size={10} /> Forget
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
