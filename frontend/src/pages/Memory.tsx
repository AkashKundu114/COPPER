import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Brain, Search, Plus, Trash2, Upload } from "lucide-react";
import { memoryAPI } from "@/services/api";
import { useMemory } from "@/hooks/useMemory";
import { Modal } from "@/components/common/Modal";

export default function Memory() {
  const [allMemories, setAllMemories] = useState<any[]>([]);
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newKey, setNewKey] = useState("");
  const [newContent, setNewContent] = useState("");
  const [stats, setStats] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { results, isSearching, search } = useMemory();

  const reload = async () => {
    const [mem, stat] = await Promise.all([memoryAPI.getAll(), memoryAPI.getStats()]);
    setAllMemories(mem.data);
    setStats(stat.data);
  };

  useEffect(() => { reload(); }, []);

  const handleSearch = () => { if (query.trim()) search(query); };

  const handleAdd = async () => {
    if (!newKey.trim() || !newContent.trim()) return;
    await memoryAPI.add(newKey, newContent);
    setShowAdd(false);
    setNewKey("");
    setNewContent("");
    reload();
  };

  const handleDelete = async (id: number) => {
    await memoryAPI.delete(id);
    setAllMemories((m) => m.filter((x) => x.id !== id));
    reload();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    form.append("source", file.name);
    try {
      await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/memory/ingest`, {
        method: "POST",
        body: form,
      });
      reload();
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-copper-400" />
          <h2 className="font-semibold text-white">Memory Bank</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="btn-ghost text-sm flex items-center gap-1.5"
          >
            <Upload size={14} />
            {uploading ? "Ingesting…" : "Ingest Doc"}
          </button>
          <input ref={fileRef} type="file" accept=".txt,.md,.pdf" className="hidden" onChange={handleFileUpload} />
          <button onClick={() => setShowAdd(true)} className="btn-copper text-sm flex items-center gap-1.5">
            <Plus size={16} /> Add Memory
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Chat Memories", value: stats.chat_memories, icon: "💬" },
            { label: "Documents", value: stats.documents, icon: "📄" },
          ].map((s) => (
            <div key={s.label} className="glass rounded-xl p-3 flex items-center gap-3">
              <span className="text-2xl">{s.icon}</span>
              <div>
                <p className="text-lg font-bold text-white">{s.value ?? 0}</p>
                <p className="text-xs text-gray-500">{s.label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search memories…"
          className="flex-1 input-copper text-sm"
        />
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="px-4 py-2 rounded-lg bg-copper-600/20 hover:bg-copper-600/40 text-copper-400 transition-colors disabled:opacity-40"
        >
          <Search size={16} />
        </button>
      </div>

      {/* Search results */}
      {results && results.chat_context && (
        <div className="glass rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wide">Search Results</p>
          <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
            {results.chat_context || "No relevant memories found."}
          </div>
        </div>
      )}

      {/* All memories */}
      <div className="space-y-2">
        <p className="text-xs text-gray-600 uppercase tracking-wide font-medium">
          Stored Memories ({allMemories.length})
        </p>
        {allMemories.length === 0 && (
          <p className="text-sm text-gray-600 text-center py-8">No memories stored yet.</p>
        )}
        {allMemories.map((m) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl p-3 flex items-start gap-3"
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-copper-400 mb-0.5">{m.key}</p>
              <p className="text-sm text-gray-300 line-clamp-2">{m.content}</p>
              <p className="text-xs text-gray-600 mt-1">
                {m.source} · {m.created_at?.slice(0, 10)}
              </p>
            </div>
            <button
              onClick={() => handleDelete(m.id)}
              className="text-gray-600 hover:text-red-400 transition-colors flex-shrink-0 mt-1"
            >
              <Trash2 size={14} />
            </button>
          </motion.div>
        ))}
      </div>

      {/* Add modal */}
      <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="Add Memory">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Key / Label</label>
            <input
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="e.g. project_overview"
              className="w-full input-copper text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Content</label>
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="What should COPPER remember?"
              rows={4}
              className="w-full input-copper text-sm resize-none"
            />
          </div>
          <button onClick={handleAdd} disabled={!newKey || !newContent} className="w-full btn-copper disabled:opacity-40">
            Save Memory
          </button>
        </div>
      </Modal>
    </div>
  );
}
