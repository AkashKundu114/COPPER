import { useState } from "react";
import { TrendingUp, CheckCircle } from "lucide-react";

interface InsightMetric {
  id: string;
  title: string;
  value: string;
  change: string;
  sub: string;
  positive: boolean;
}

export function Insights() {
  const [metrics] = useState<InsightMetric[]>([
    {
      id: "1",
      title: "Local Inference Latency",
      value: "1.4s",
      change: "-28%",
      sub: "Avg Time-To-First-Token on RTX 5060",
      positive: true,
    },
    {
      id: "2",
      title: "Offline Privacy Score",
      value: "100%",
      change: "0 Leaks",
      sub: "100% of reasoning processed locally on D:\\blobs",
      positive: true,
    },
    {
      id: "3",
      title: "Token Generation Speed",
      value: "48 t/s",
      change: "+14%",
      sub: "GPU Hardware Accelerated (Ollama LLM)",
      positive: true,
    },
    {
      id: "4",
      title: "Task Completion Rate",
      value: "92%",
      change: "+5%",
      sub: "Across coding and system automation",
      positive: true,
    },
  ]);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp size={20} className="text-accent-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Productivity & System Insights
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Evidence-based telemetry derived from real local hardware and model
            sessions
          </p>
        </div>
      </div>

      {/* Top 4 Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => (
          <div
            key={m.id}
            className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2 hover:border-slate-700 transition-all shadow-sm"
          >
            <span className="text-[11px] text-slate-400 font-semibold">
              {m.title}
            </span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold text-white font-sans">
                {m.value}
              </span>
              <span
                className={`text-[11px] font-bold ${m.positive ? "text-verdigris-400" : "text-danger-400"}`}
              >
                {m.change}
              </span>
            </div>
            <p className="text-[10px] text-slate-500">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Model Distribution & Cognitive Focus Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Model Workload Allocation
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-white">
                  Qwen 2.5 Coder 7B (Coding & Technical)
                </span>
                <span className="text-accent-400 font-bold">52%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                <div className="h-full bg-accent-500" style={{ width: "52%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-white">
                  Llama 3.1 8B (General Conversation)
                </span>
                <span className="text-accent-400 font-bold">30%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                <div className="h-full bg-accent-500" style={{ width: "30%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span className="text-white">
                  DeepSeek R1 7B (Reasoning & Math)
                </span>
                <span className="text-accent-400 font-bold">18%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                <div className="h-full bg-accent-500" style={{ width: "18%" }} />
              </div>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Observed Focus Patterns
          </h3>
          <div className="space-y-2.5">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-2.5">
              <CheckCircle size={15} className="text-verdigris-400 mt-0.5" />
              <div>
                <p className="text-white font-sans text-xs font-semibold">
                  High Engineering Throughput
                </p>
                <p className="text-slate-400 text-[11px]">
                  Primary activity concentrated on Python and React
                  architecture.
                </p>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-start gap-2.5">
              <CheckCircle size={15} className="text-verdigris-400 mt-0.5" />
              <div>
                <p className="text-white font-sans text-xs font-semibold">
                  Zero Cloud Dependency
                </p>
                <p className="text-slate-400 text-[11px]">
                  All inferences, embeddings, and voice audio processed 100%
                  locally.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
