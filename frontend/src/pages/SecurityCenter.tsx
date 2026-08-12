import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Download, Trash2, Cloud, Lock } from "lucide-react";
import { auditAPI } from "@/services/api";

interface AuditEntry {
  id: number;
  category: string;
  actor: string;
  summary: string;
  detail?: string;
  scope: "local" | "cloud";
  created_at: string;
}

export default function SecurityCenter() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const load = async () => {
    const { data } = await auditAPI.list(filter || undefined);
    setEntries(data);
  };

  useEffect(() => { load(); }, [filter]);

  const exportData = async () => {
    const res = await auditAPI.exportData();
    const url = URL.createObjectURL(res.data as Blob);
    const a = document.createElement("a");
    a.href = url; a.download = "copper-data-export.json"; a.click();
    URL.revokeObjectURL(url);
  };

  const deleteAll = async () => {
    if (!confirmingDelete) { setConfirmingDelete(true); return; }
    await auditAPI.deleteAllData(true);
    setConfirmingDelete(false);
    load();
  };

  const CATEGORIES = [
    "", "guardian_challenge", "guardian_safety_block", "external_api_accessed",
    "tool_executed", "memory_created", "memory_deleted", "agent_activated", "agent_rolled_back",
  ];

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2">
        <ShieldCheck size={20} className="text-copper-400" />
        <h2 className="font-semibold text-white">Security Center</h2>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="glass rounded-xl p-4 flex items-center gap-3">
          <Lock size={18} className="text-green-400" />
          <div>
            <p className="text-sm text-white font-medium">Local-first</p>
            <p className="text-xs text-gray-500">Ollama is the default provider</p>
          </div>
        </div>
        <div className="glass rounded-xl p-4 flex items-center gap-3">
          <Cloud size={18} className="text-blue-400" />
          <div>
            <p className="text-sm text-white font-medium">Cloud calls are logged</p>
            <p className="text-xs text-gray-500">Every OpenAI request is redacted first</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}
          className="bg-dark-700 border border-copper-600/30 text-white text-xs rounded-lg px-3 py-1.5 outline-none">
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c || "All categories"}</option>
          ))}
        </select>
        <div className="flex gap-2">
          <button onClick={exportData} className="btn-ghost text-xs flex items-center gap-1.5">
            <Download size={12} /> Export my data
          </button>
          <button onClick={deleteAll}
            className={`text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors ${
              confirmingDelete
                ? "border-red-500 bg-red-500/20 text-red-300"
                : "border-red-500/30 text-red-400 hover:bg-red-500/10"
            }`}>
            <Trash2 size={12} /> {confirmingDelete ? "Confirm delete all?" : "Delete all data"}
          </button>
        </div>
      </div>

      <div className="space-y-1.5">
        {entries.length === 0 && (
          <p className="text-sm text-gray-600 text-center py-8">No audit events yet.</p>
        )}
        {entries.map((e) => (
          <motion.div key={e.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="glass rounded-lg px-3 py-2 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs text-gray-300">{e.summary}</p>
              <p className="text-2xs text-gray-600 font-mono mt-0.5">
                {e.actor} · {e.category} · {new Date(e.created_at).toLocaleString()}
              </p>
            </div>
            <span className={`flex-shrink-0 text-2xs px-2 py-0.5 rounded-full ${
              e.scope === "cloud" ? "bg-blue-600/20 text-blue-400" : "bg-green-600/20 text-green-400"
            }`}>
              {e.scope}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
