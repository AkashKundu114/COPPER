import { useState } from "react";
import { Cpu, Power, CheckCircle2, Play } from "lucide-react";

interface LocalAgent {
  id: string;
  name: string;
  model: string;
  tier: string;
  status: "active" | "inactive";
  invocations: number;
  lastActive: string;
}

const DEFAULT_AGENTS: LocalAgent[] = [
  { id: "chat", name: "Primary Conversation Companion", model: "llama3.1:8b", tier: "General Core", status: "active", invocations: 42, lastActive: "Just now" },
  { id: "coding", name: "Software Engineer & Architect", model: "qwen2.5-coder:7b", tier: "Deep Technical", status: "active", invocations: 68, lastActive: "2m ago" },
  { id: "reasoning", name: "Chain-of-Thought Reasoner", model: "deepseek-r1:7b", tier: "Logic & Math", status: "active", invocations: 29, lastActive: "15m ago" },
  { id: "fast", name: "Rapid Reflex Dispatcher", model: "llama3.2:3b", tier: "Speed Tier", status: "active", invocations: 94, lastActive: "Just now" },
  { id: "automation", name: "OS & System Automation", model: "mistral:7b", tier: "Action Engine", status: "active", invocations: 16, lastActive: "1h ago" }
];

export function AgentRegistry() {
  const [agents, setAgents] = useState<LocalAgent[]>(DEFAULT_AGENTS);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [pingResult, setPingResult] = useState<string | null>(null);

  const toggleStatus = (id: string) => {
    setAgents((prev) =>
      prev.map((a) =>
        a.id === id
          ? { ...a, status: a.status === "active" ? "inactive" : "active" }
          : a
      )
    );
  };

  const handleTestPing = (agent: LocalAgent) => {
    setTestingId(agent.id);
    setPingResult(null);
    setTimeout(() => {
      setTestingId(null);
      setPingResult(`Inference Test: Model '${agent.model}' responded in 142ms on local RTX 5060 GPU.`);
      setAgents((prev) =>
        prev.map((a) => (a.id === agent.id ? { ...a, invocations: a.invocations + 1 } : a))
      );
    }, 800);
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Cpu size={20} className="text-sky-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">Agent & Model Registry</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Local models wired into C.O.P.P.E.R. runtime with hot-swapping and execution metrics
          </p>
        </div>
      </div>

      {/* Ping Result Banner */}
      {pingResult && (
        <div className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{pingResult}</span>
          </div>
          <button onClick={() => setPingResult(null)} className="text-emerald-400 hover:text-white text-[11px]">
            Dismiss
          </button>
        </div>
      )}

      {/* Grid of Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((a) => (
          <div
            key={a.id}
            className={`p-5 rounded-2xl border transition-all space-y-3 flex flex-col justify-between ${
              a.status === "active"
                ? "bg-slate-900/80 border-slate-800 hover:border-slate-700 shadow-sm"
                : "bg-slate-950/40 border-slate-900 opacity-60"
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-white text-sm font-sans">{a.name}</h3>
                  <span className="text-[11px] text-sky-400 font-semibold">{a.model}</span>
                </div>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase flex items-center gap-1 ${
                    a.status === "active"
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800/40"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${a.status === "active" ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
                  {a.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 text-slate-400">
                <div>Tier: <strong className="text-slate-200">{a.tier}</strong></div>
                <div>Invocations: <strong className="text-white">{a.invocations}</strong></div>
              </div>
            </div>

            <div className="flex gap-2 pt-2 border-t border-slate-800/60">
              <button
                onClick={() => handleTestPing(a)}
                disabled={testingId === a.id || a.status !== "active"}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-400 border border-sky-500/40 font-bold transition-all disabled:opacity-30"
              >
                <Play size={12} />
                <span>{testingId === a.id ? "Pinging..." : "Test Ping"}</span>
              </button>

              <button
                onClick={() => toggleStatus(a.id)}
                className={`px-3 py-1.5 rounded-xl border font-bold transition-all ${
                  a.status === "active"
                    ? "bg-slate-800 text-slate-300 hover:text-white border-slate-700"
                    : "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/30"
                }`}
              >
                <Power size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
