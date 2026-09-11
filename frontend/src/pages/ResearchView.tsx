import React, { useState, useEffect } from "react";
import {
  Search,
  BookOpen,
  Sparkles,
  Clock,
  Download,
  Copy,
  Check,
  ExternalLink,
  Layers,
  RefreshCw,
} from "lucide-react";
import { researchAPI } from "../services/api";

interface ResearchSource {
  url: string;
  title: string;
  snippet: string;
  relevance_score?: number;
}

interface ResearchReport {
  report_id: string;
  topic: string;
  status: "in_progress" | "completed" | "failed" | "cancelled";
  started_at: string;
  completed_at?: string;
  deadline?: string;
  sources: ResearchSource[];
  sections: Array<{ title: string; content: string }>;
  executive_summary: string;
  markdown_report: string;
  progress_pct: number;
  error?: string;
}

export const ResearchView: React.FC = () => {
  const [reports, setReports] = useState<ResearchReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [copied, setCopied] = useState(false);

  // Start Research Form
  const [topic, setTopic] = useState("");
  const [depth, setDepth] = useState<"quick" | "standard" | "deep">("standard");
  const [deadline, setDeadline] = useState("");
  const [searchFilter, setSearchFilter] = useState("");

  const loadReports = async () => {
    try {
      const res = await researchAPI.getReports();
      if (Array.isArray(res.data)) {
        setReports(res.data);
        if (selectedReport) {
          const updated = res.data.find((r: ResearchReport) => r.report_id === selectedReport.report_id);
          if (updated) setSelectedReport(updated);
        }
      }
    } catch (err) {
      console.error("Failed to load research reports:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
    const interval = setInterval(loadReports, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleStartResearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setStarting(true);
    try {
      const res = await researchAPI.start(topic.trim(), depth, deadline || undefined);
      setTopic("");
      setDeadline("");
      await loadReports();
      if (res.data?.report_id) {
        const full = await researchAPI.getReport(res.data.report_id);
        if (full.data) setSelectedReport(full.data);
      }
    } catch (err) {
      console.error("Failed to start research:", err);
    } finally {
      setStarting(false);
    }
  };

  const handleCancelResearch = async (reportId: string) => {
    try {
      await researchAPI.cancel(reportId);
      loadReports();
    } catch (err) {
      console.error("Failed to cancel research:", err);
    }
  };

  const handleCopyMarkdown = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportMarkdown = (report: ResearchReport) => {
    const blob = new Blob([report.markdown_report || report.executive_summary], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `research-${report.topic.toLowerCase().replace(/[^a-z0-9]/g, "-")}.md`;
    a.click();
  };

  const filteredReports = reports.filter((r) =>
    r.topic.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const activeReports = reports.filter((r) => r.status === "in_progress");

  return (
    <div className="modern-page p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BookOpen size={20} className="text-cyber-cyan" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Autonomous Deep Research Hub
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Multi-source web synthesis, citation extraction, and structured research dossiers
          </p>
        </div>
        <button
          onClick={loadReports}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all text-xs font-mono"
        >
          <RefreshCw size={13} className={loading ? "animate-spin text-cyber-cyan" : ""} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Start Research Card */}
      <form
        onSubmit={handleStartResearch}
        className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm"
      >
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-accent-400" />
          <h2 className="text-xs font-bold text-white font-sans uppercase tracking-wider">
            Initiate Autonomous Research
          </h2>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-[10px] text-slate-400 block mb-1">
              Research Objective / Topic
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Compare Rust vs Go memory models in high-concurrency stream processing"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white font-mono text-xs focus:outline-none focus:border-cyber-cyan transition-colors"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-slate-400 block mb-1">
                Investigation Depth
              </label>
              <div className="flex gap-2">
                {(["quick", "standard", "deep"] as const).map((d) => (
                  <button
                    type="button"
                    key={d}
                    onClick={() => setDepth(d)}
                    className={`flex-1 py-1.5 rounded-lg capitalize text-xs font-bold transition-all border ${
                      depth === d
                        ? "bg-accent-500/20 text-accent-400 border-accent-500/50 shadow-sm"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 block mb-1">
                Target Completion Time (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Today 5:00 PM or 2 hours"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white font-mono text-xs focus:outline-none focus:border-cyber-cyan transition-colors"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={starting || !topic.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20 disabled:opacity-50"
          >
            <Sparkles size={14} />
            <span>{starting ? "Starting Pipeline..." : "Dispatch Research Agent"}</span>
          </button>
        </div>
      </form>

      {/* Active Investigations In Progress */}
      {activeReports.length > 0 && (
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-cyan-500/30 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white font-sans flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping" />
              Active Research Pipelines ({activeReports.length})
            </span>
          </div>

          <div className="space-y-2.5">
            {activeReports.map((r) => (
              <div
                key={r.report_id}
                className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs font-sans">{r.topic}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-cyber-cyan font-bold bg-cyber-cyan/10 px-2 py-0.5 rounded-full border border-cyber-cyan/30">
                      {r.progress_pct}%
                    </span>
                    <button
                      onClick={() => handleCancelResearch(r.report_id)}
                      className="text-danger-400 hover:text-danger-300 text-[10px] underline ml-2"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-accent-500 transition-all duration-500"
                    style={{ width: `${r.progress_pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reports Library & Viewer Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left Column: Reports List */}
        <div className="lg:col-span-1 p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 h-[520px] flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-bold text-white font-sans uppercase tracking-wider">
              Research Dossiers ({reports.length})
            </h3>
          </div>

          <div className="relative">
            <Search size={13} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search reports..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-[11px] text-white focus:outline-none focus:border-cyber-cyan"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {filteredReports.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No reports found. Start an autonomous research mission above.
              </div>
            ) : (
              filteredReports.map((r) => {
                const isSelected = selectedReport?.report_id === r.report_id;
                return (
                  <div
                    key={r.report_id}
                    onClick={() => setSelectedReport(r)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer space-y-1.5 ${
                      isSelected
                        ? "bg-cyber-cyan/10 border-cyber-cyan/50 shadow-sm"
                        : "bg-slate-950/80 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-xs truncate max-w-[180px] font-sans">
                        {r.topic}
                      </span>
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                          r.status === "completed"
                            ? "bg-verdigris/10 text-verdigris border-verdigris/30"
                            : r.status === "in_progress"
                              ? "bg-cyber-cyan/10 text-cyber-cyan border-cyber-cyan/30"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {r.status}
                      </span>
                    </div>

                    <p className="text-[10px] text-slate-400 line-clamp-2">
                      {r.executive_summary || "Autonomous investigation underway..."}
                    </p>

                    <div className="flex items-center justify-between text-[9px] text-slate-500 pt-1 border-t border-slate-900">
                      <span>{r.sources?.length || 0} Sources</span>
                      <span>{new Date(r.started_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Report Dossier Viewer */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col h-[520px] overflow-hidden">
          {selectedReport ? (
            <div className="flex flex-col h-full space-y-4">
              {/* Report Header */}
              <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-white font-sans">
                      {selectedReport.topic}
                    </h2>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Clock size={11} /> Started: {new Date(selectedReport.started_at).toLocaleTimeString()}
                    </span>
                    <span>•</span>
                    <span>{selectedReport.sources?.length || 0} External Citations</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleCopyMarkdown(selectedReport.markdown_report || selectedReport.executive_summary)}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-all"
                    title="Copy Markdown"
                  >
                    {copied ? <Check size={12} className="text-verdigris" /> : <Copy size={12} />}
                    <span>{copied ? "Copied" : "Copy"}</span>
                  </button>
                  <button
                    onClick={() => handleExportMarkdown(selectedReport)}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all"
                    title="Download Report as Markdown"
                  >
                    <Download size={12} />
                    <span>Export</span>
                  </button>
                </div>
              </div>

              {/* Report Body */}
              <div className="flex-1 overflow-y-auto space-y-4 pr-1 custom-scrollbar">
                {/* Executive Summary */}
                {selectedReport.executive_summary && (
                  <div className="p-4 rounded-xl bg-cyber-cyan/5 border border-cyber-cyan/20 space-y-1.5">
                    <span className="text-[10px] font-bold text-cyber-cyan uppercase tracking-wider block font-sans">
                      Executive Synthesis
                    </span>
                    <p className="text-xs text-slate-200 leading-relaxed">
                      {selectedReport.executive_summary}
                    </p>
                  </div>
                )}

                {/* Markdown Report Content */}
                {selectedReport.markdown_report ? (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-3">
                    <pre className="text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                      {selectedReport.markdown_report}
                    </pre>
                  </div>
                ) : (
                  <div className="p-8 text-center text-slate-500 text-xs">
                    Synthesizing complete dossier... {selectedReport.progress_pct}% complete.
                  </div>
                )}

                {/* Sources & Citations */}
                {selectedReport.sources && selectedReport.sources.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-sans">
                      Referenced Citations & Sources
                    </h4>
                    <div className="space-y-1.5">
                      {selectedReport.sources.map((src, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/60 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2 truncate max-w-[400px]">
                            <span className="text-[10px] text-accent-400 font-bold">[{idx + 1}]</span>
                            <span className="text-white font-medium truncate">{src.title || src.url}</span>
                          </div>
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-cyber-cyan hover:underline text-[10px]"
                          >
                            <span>Open</span>
                            <ExternalLink size={10} />
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-500 space-y-2">
              <Layers size={32} className="text-slate-700" />
              <p className="text-xs font-semibold text-slate-400">No Research Dossier Selected</p>
              <p className="text-[11px] text-slate-500 max-w-sm">
                Select an existing investigation from the left sidebar or start a new deep research run.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
