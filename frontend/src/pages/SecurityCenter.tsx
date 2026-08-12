import { useEffect, useState } from "react";
import { ShieldCheck, Download, Trash2, Cloud, Lock } from "lucide-react";
import { fetchLogs } from "../lib/api";

interface AuditEntry {
  id: number;
  category: string;
  actor: string;
  summary: string;
  detail?: string;
  scope: "local" | "cloud";
  created_at: string;
}

export function SecurityCenter() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  const load = async () => {
    try {
      const data = await fetchLogs(filter || undefined);
      setEntries(data as any);
    } catch {
      setEntries([]);
    }
  };

  useEffect(() => {
    load();
  }, [filter]);

  const CATEGORIES = [
    "",
    "guardian_challenge",
    "guardian_safety_block",
    "external_api_accessed",
    "tool_executed",
    "memory_created",
    "memory_deleted",
    "agent_activated",
    "agent_rolled_back",
  ];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div className="flex items-center gap-2">
        <ShieldCheck size={20} className="text-[#ff5722]" />
        <h1 className="text-xl font-bold text-white tracking-tight">Security & Privacy Center</h1>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 flex items-center gap-3">
          <Lock size={18} className="text-emerald-400" />
          <div>
            <p className="text-xs text-white font-bold font-mono">100% Local-First</p>
            <p className="text-[11px] text-gray-400 font-mono">Ollama is the default offline provider</p>
          </div>
        </div>
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 flex items-center gap-3">
          <Cloud size={18} className="text-blue-400" />
          <div>
            <p className="text-xs text-white font-bold font-mono">Zero-Trust Firewall Log</p>
            <p className="text-[11px] text-gray-400 font-mono">Every external request is redacted & audited</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2 font-mono text-xs">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-[#14141a] border border-white/10 text-white rounded-lg px-3 py-1.5 outline-none"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c || "All Categories"}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <button className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-gray-300 hover:text-white flex items-center gap-1.5 transition-all">
            <Download size={12} /> Export Audit Log
          </button>
          <button
            onClick={() => setConfirmingDelete(!confirmingDelete)}
            className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition-all ${
              confirmingDelete
                ? "border-red-500 bg-red-950/60 text-red-300"
                : "border-red-500/30 text-red-400 hover:bg-red-950/30"
            }`}
          >
            <Trash2 size={12} /> {confirmingDelete ? "Confirm Wipe All Data?" : "Wipe All Data"}
          </button>
        </div>
      </div>

      <div className="space-y-2 font-mono text-xs">
        {entries.length === 0 && (
          <div className="p-6 rounded-xl bg-[#14141a] border border-white/10 text-center text-xs text-gray-400 space-y-1">
            <p>No audit events logged yet. All actions executing locally within private boundary.</p>
          </div>
        )}
        {entries.map((e) => (
          <div key={e.id} className="p-3 rounded-lg bg-[#14141a] border border-white/10 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs text-gray-200">{e.summary}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">
                {e.actor} · {e.category} · {new Date(e.created_at).toLocaleString()}
              </p>
            </div>
            <span
              className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                e.scope === "cloud" ? "bg-blue-950 text-blue-400 border border-blue-500/30" : "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
              }`}
            >
              {e.scope}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
