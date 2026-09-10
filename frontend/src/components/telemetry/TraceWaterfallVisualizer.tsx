import React, { useState } from "react";
import {
  Clock,
  ExternalLink,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  GitCommit,
  ShieldCheck,
  Compass,
  Cpu,
  Send,
  Radio,
} from "lucide-react";
import type { DistributedTrace, TraceSpan } from "../../lib/api";

interface TraceWaterfallVisualizerProps {
  trace: DistributedTrace;
  defaultExpanded?: boolean;
}

export const TraceWaterfallVisualizer: React.FC<TraceWaterfallVisualizerProps> = ({
  trace,
  defaultExpanded = true,
}) => {
  const [copied, setCopied] = useState(false);
  const [expandedSpanId, setExpandedSpanId] = useState<string | null>(null);
  const [isFullViewExpanded, setIsFullViewExpanded] = useState(defaultExpanded);

  const copyTraceId = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(trace.trace_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSpanIcon = (name: string) => {
    switch (name) {
      case "copper.websocket.request":
      case "copper.http.request":
        return <Radio size={12} className="text-purple-400" />;
      case "copper.router":
        return <Compass size={12} className="text-indigo-400" />;
      case "copper.guardian":
        return <ShieldCheck size={12} className="text-amber-400" />;
      case "copper.agent":
        return <GitCommit size={12} className="text-cyan-400" />;
      case "copper.llm":
        return <Cpu size={12} className="text-emerald-400" />;
      case "copper.response":
        return <Send size={12} className="text-blue-400" />;
      default:
        return <Clock size={12} className="text-slate-400" />;
    }
  };

  const getSpanColor = (name: string) => {
    switch (name) {
      case "copper.websocket.request":
      case "copper.http.request":
        return "bg-purple-500/80 border-purple-400";
      case "copper.router":
        return "bg-indigo-500/80 border-indigo-400";
      case "copper.guardian":
        return "bg-amber-500/80 border-amber-400";
      case "copper.agent":
        return "bg-cyan-500/80 border-cyan-400";
      case "copper.llm":
        return "bg-emerald-500/80 border-emerald-400";
      case "copper.response":
        return "bg-blue-500/80 border-blue-400";
      default:
        return "bg-slate-500/80 border-slate-400";
    }
  };

  const maxDuration = Math.max(trace.duration_ms, 0.1);

  return (
    <div className="rounded-xl bg-slate-950/90 border border-slate-800/80 overflow-hidden font-mono text-xs shadow-md">
      {/* Header bar */}
      <div
        onClick={() => setIsFullViewExpanded(!isFullViewExpanded)}
        className="p-3.5 bg-slate-900/90 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3 cursor-pointer select-none hover:bg-slate-900 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <button className="text-slate-400 hover:text-white">
            {isFullViewExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
          </button>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-950/70 border border-purple-800/50 text-purple-300 uppercase tracking-wide">
            OpenTelemetry
          </span>
          <div className="flex items-center gap-1.5 font-sans font-bold text-white text-xs">
            <span>{trace.root_name}</span>
          </div>
          <span className="text-[11px] text-slate-400">
            ({trace.spans_count} spans • {trace.duration_ms}ms)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Trace ID badge with copy */}
          <div
            onClick={copyTraceId}
            title="Click to copy Trace ID"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800/80 border border-slate-800 text-[11px] text-slate-300 hover:text-white transition-all cursor-pointer"
          >
            <span className="text-slate-500">Trace:</span>
            <span className="font-mono text-purple-300">
              {trace.trace_id.slice(0, 8)}...{trace.trace_id.slice(-6)}
            </span>
            {copied ? (
              <Check size={12} className="text-emerald-400" />
            ) : (
              <Copy size={12} className="text-slate-400" />
            )}
          </div>

          {/* Grafana Tempo Deep-Link */}
          <a
            href={trace.grafana_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-950/70 hover:bg-indigo-900 border border-indigo-700/50 text-[11px] text-indigo-200 font-sans font-semibold transition-all hover:shadow-lg hover:shadow-indigo-950/50"
          >
            <span>View in Tempo</span>
            <ExternalLink size={11} />
          </a>
        </div>
      </div>

      {/* Waterfall Body */}
      {isFullViewExpanded && (
        <div className="p-3.5 space-y-3">
          {/* Time axis header */}
          <div className="flex items-center text-[10px] text-slate-500 border-b border-slate-800/60 pb-1.5 pl-[200px]">
            <div className="w-1/4">0ms</div>
            <div className="w-1/4 text-center">{Math.round(maxDuration * 0.33)}ms</div>
            <div className="w-1/4 text-center">{Math.round(maxDuration * 0.66)}ms</div>
            <div className="w-1/4 text-right">{Math.round(maxDuration)}ms</div>
          </div>

          {/* Span rows */}
          <div className="space-y-1.5">
            {trace.spans.map((span: TraceSpan) => {
              const offsetMs = span.offset_ms || 0;
              const leftPercent = Math.min(100, Math.max(0, (offsetMs / maxDuration) * 100));
              const widthPercent = Math.min(
                100 - leftPercent,
                Math.max(2, (span.duration_ms / maxDuration) * 100)
              );
              const isSelected = expandedSpanId === span.span_id;
              const isChild = span.parent_id !== null;

              return (
                <div key={span.span_id} className="space-y-1">
                  <div
                    onClick={() => setExpandedSpanId(isSelected ? null : span.span_id)}
                    className={`flex items-center gap-3 p-1.5 rounded-lg hover:bg-slate-900/80 cursor-pointer transition-colors ${
                      isSelected ? "bg-slate-900 border border-slate-800" : ""
                    }`}
                  >
                    {/* Span label */}
                    <div
                      className={`w-[200px] shrink-0 flex items-center gap-1.5 text-[11px] truncate ${
                        isChild ? "pl-4 text-slate-300" : "font-bold text-white"
                      }`}
                    >
                      {getSpanIcon(span.name)}
                      <span className="truncate">{span.name.replace("copper.", "")}</span>
                      <span className="text-[10px] text-slate-500 ml-auto mr-1">
                        {span.duration_ms}ms
                      </span>
                    </div>

                    {/* Timeline bar area */}
                    <div className="flex-1 relative h-5 bg-slate-900/40 rounded overflow-hidden">
                      {/* Grid background markers */}
                      <div className="absolute inset-0 grid grid-cols-4 pointer-events-none opacity-10 border-x border-slate-700" />

                      {/* Span timing bar */}
                      <div
                        style={{
                          left: `${leftPercent}%`,
                          width: `${widthPercent}%`,
                        }}
                        className={`absolute top-0.5 bottom-0.5 rounded border text-[9px] text-white flex items-center px-1.5 font-sans font-medium transition-all ${getSpanColor(
                          span.name
                        )}`}
                      >
                        <span className="truncate drop-shadow-sm">
                          {span.duration_ms > 10 ? `${span.duration_ms}ms` : ""}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Expandable attributes drawer for this span */}
                  {isSelected && (
                    <div className="ml-[200px] p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] space-y-1.5 animate-in fade-in duration-150">
                      <div className="flex items-center justify-between text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                        <span>Span: {span.name}</span>
                        <span>ID: {span.span_id}</span>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[10px]">
                        <div>
                          <span className="text-slate-500">Duration:</span>{" "}
                          <span className="text-emerald-400 font-bold">{span.duration_ms}ms</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Offset:</span>{" "}
                          <span className="text-slate-300">{span.offset_ms}ms</span>
                        </div>
                        <div>
                          <span className="text-slate-500">Status:</span>{" "}
                          <span
                            className={
                              span.status === "ERROR" ? "text-rose-400 font-bold" : "text-slate-300"
                            }
                          >
                            {span.status}
                          </span>
                        </div>
                      </div>

                      {span.attributes && Object.keys(span.attributes).length > 0 && (
                        <div>
                          <div className="text-[10px] text-slate-500 font-bold mt-1">Attributes:</div>
                          <pre className="p-2 rounded bg-slate-950 border border-slate-800 text-[10px] text-cyan-300 overflow-x-auto max-h-40">
                            {JSON.stringify(span.attributes, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
