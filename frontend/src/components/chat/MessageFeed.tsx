import { useEffect, useRef, useState } from "react";
import {
  type ChatLine,
  type ActiveTaskGraphTrace,
  type MessageMetrics,
  type ComputerUseStep,
} from "../../hooks/useBrainSocket";
import { type AgentStats, type ParsedDocument } from "../../lib/api";
import {
  FileText,
  BookOpen,
  FileCode,
  Table,
  Braces,
  Check,
  Cpu,
  Zap,
  Layers,
  Timer,
  Clock,
  Copy,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MarkdownContent } from "./MarkdownContent";
import { DocumentReaderModal } from "../documents/DocumentReaderModal";
import { TaskGraphVisualizer } from "./TaskGraphVisualizer";
import { ComputerUseVisualizer } from "./ComputerUseVisualizer";

interface MessageFeedProps {
  lines: ChatLine[];
  agentStats: Record<string, AgentStats>;
  thinking: boolean;
  activeAgent: string | null;
  activeTaskGraph?: ActiveTaskGraphTrace | null;
  activeComputerUse?: ComputerUseStep[] | null;
  lastCorrectionAck?: { id: string; summary: string; timestamp: number } | null;
}

interface ParsedAttachment {
  filename: string;
  meta: string;
  lang: string;
  content: string;
}

function parseAttachments(text: string): { cleanText: string; attachments: ParsedAttachment[] } {
  const attachmentRegex = /--- Attached File: (.*?) ---\n```([\s\S]*?)\n```/g;
  const attachments: ParsedAttachment[] = [];
  let match;

  while ((match = attachmentRegex.exec(text)) !== null) {
    const fullHeader = match[1].trim();
    const codeBlock = match[2];

    const firstNewline = codeBlock.indexOf("\n");
    let lang = "";
    let content = codeBlock;
    if (firstNewline !== -1) {
      const potentialLang = codeBlock.slice(0, firstNewline).trim();
      if (/^[a-zA-Z0-9_-]+$/.test(potentialLang)) {
        lang = potentialLang;
        content = codeBlock.slice(firstNewline + 1);
      }
    }

    attachments.push({
      filename: fullHeader.split(" ")[0] || "document.txt",
      meta: fullHeader,
      lang,
      content,
    });
  }

  const cleanText = text.replace(/--- Attached File: [\s\S]*?```/g, "").trim();
  return { cleanText, attachments };
}

function CorrectionAckPill({ summary, onFade }: { summary: string; onFade: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onFade, 5000);
    return () => clearTimeout(timer);
  }, [onFade]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      title={summary}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-verdigris-400 bg-verdigris-950/30 border border-verdigris-800/30 rounded-full w-fit ml-0 mt-1 mb-2"
    >
      <Check className="w-3 h-3" />
      <span>Noted — updating</span>
    </motion.div>
  );
}

function MessageMetricsBar({ metrics, text }: { metrics: MessageMetrics; text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedTtft =
    metrics.ttft_ms < 1000
      ? `${Math.round(metrics.ttft_ms)}ms`
      : `${(metrics.ttft_ms / 1000).toFixed(2)}s`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 3 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-wrap items-center gap-2 pt-2 pb-1 font-mono text-[11px] text-zinc-400 select-none border-t border-white/5 mt-1"
    >
      {/* Model Selected */}
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 transition-colors shadow-sm"
        title={`Model Selected: ${metrics.model}`}
      >
        <Cpu size={12} className="text-accent-400" />
        <span className="font-semibold text-accent-300 font-sans tracking-tight">{metrics.model}</span>
      </div>

      {/* Tokens / Sec */}
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 transition-colors shadow-sm"
        title={`Throughput: ${metrics.tokens_per_sec} tokens/second`}
      >
        <Zap size={12} className="text-amber-400" />
        <span>
          <strong className="text-white">{metrics.tokens_per_sec}</strong> tok/s
        </span>
      </div>

      {/* Total Tokens (with Prompt / Completion breakdown) */}
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 transition-colors shadow-sm"
        title={`Total Tokens: ${metrics.total_tokens} (${metrics.prompt_tokens} prompt + ${metrics.completion_tokens} completion)`}
      >
        <Layers size={12} className="text-purple-400" />
        <span>
          <strong className="text-white">{metrics.total_tokens}</strong> toks
        </span>
        <span className="text-[9.5px] text-zinc-500 font-mono">
          ({metrics.prompt_tokens}p · {metrics.completion_tokens}c)
        </span>
      </div>

      {/* Time to First Token (TTFT) */}
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 transition-colors shadow-sm"
        title={`Time to First Token: ${formattedTtft}`}
      >
        <Timer size={12} className="text-sky-400" />
        <span>
          TTFT: <strong className="text-white">{formattedTtft}</strong>
        </span>
      </div>

      {/* Total Time Taken */}
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-zinc-300 transition-colors shadow-sm"
        title={`Total Generation Time: ${metrics.total_time_sec}s`}
      >
        <Clock size={12} className="text-emerald-400" />
        <span>
          Total: <strong className="text-white">{metrics.total_time_sec}s</strong>
        </span>
      </div>

      {/* Copy Response Button */}
      <button
        type="button"
        onClick={handleCopy}
        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-transparent hover:bg-white/5 border border-transparent hover:border-white/10 text-zinc-400 hover:text-zinc-200 transition-all ml-auto"
        title="Copy response markdown"
      >
        {copied ? (
          <>
            <Check size={12} className="text-emerald-400" />
            <span className="text-[10px] text-emerald-400">Copied</span>
          </>
        ) : (
          <>
            <Copy size={12} />
            <span className="text-[10px]">Copy</span>
          </>
        )}
      </button>
    </motion.div>
  );
}

export function MessageFeed({
  lines,
  agentStats,
  thinking,
  activeAgent,
  activeTaskGraph,
  activeComputerUse,
  lastCorrectionAck,
}: MessageFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);
  const [selectedDoc, setSelectedDoc] = useState<ParsedDocument | null>(null);
  const [showCorrection, setShowCorrection] = useState<{ id: string; summary: string } | null>(null);

  useEffect(() => {
    if (lastCorrectionAck && (Date.now() - lastCorrectionAck.timestamp < 6000)) {
      setShowCorrection(lastCorrectionAck);
    }
  }, [lastCorrectionAck]);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [lines, thinking, activeTaskGraph, activeComputerUse]);

  const openAttachmentReader = (att: ParsedAttachment) => {
    const ext = att.filename.split(".").pop()?.toLowerCase() || "txt";
    const lines = att.content.split("\n");
    const words = att.content.split(/\s+/).filter(Boolean);
    const sizeBytes = new Blob([att.content]).size;
    const sizeFormatted =
      sizeBytes > 1024 * 1024
        ? `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
        : `${(sizeBytes / 1024).toFixed(1)} KB`;

    const doc: ParsedDocument = {
      filename: att.filename,
      extension: ext,
      category: ext.toUpperCase() + " File",
      size_bytes: sizeBytes,
      size_formatted: sizeFormatted,
      page_count: 1,
      line_count: lines.length,
      word_count: words.length,
      char_count: att.content.length,
      estimated_tokens: Math.max(1, Math.floor(att.content.length / 4)),
      indexed_chunks: 1,
      pages: [{ page_number: 1, text: att.content, word_count: words.length, char_count: att.content.length }],
      full_text: att.content,
      preview_text: att.content.slice(0, 500),
      status: "success",
    };
    setSelectedDoc(doc);
  };

  const getDocIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    if (ext === "pdf") return BookOpen;
    if (ext === "csv" || ext === "tsv") return Table;
    if (ext === "json") return Braces;
    if (["py", "js", "ts", "tsx", "jsx", "html", "css", "sql", "rs", "go", "java", "c", "cpp"].includes(ext)) {
      return FileCode;
    }
    return FileText;
  };

  return (
    <div
      ref={feedRef}
      className="flex-1 w-full max-w-[850px] mx-auto overflow-y-auto px-4 py-8 space-y-6 custom-scrollbar"
    >
      {selectedDoc && (
        <DocumentReaderModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}

      {lines.map((line, i) => {
        const isUser = line.agent === "YOU" || line.agent === "user";
        const { cleanText, attachments } = isUser ? parseAttachments(line.text) : { cleanText: line.text, attachments: [] };

        const isLastAssistant = i === lines.reduce((acc, l, idx) => (l.agent !== "YOU" && l.agent !== "user" ? idx : acc), -1);

        if (isUser) {
          return (
            <div key={line.id || i} className="flex justify-end w-full animate-slide-up mb-8 mt-4">
              <div className="relative bg-[#070d18]/90 backdrop-blur-xl text-text px-4 py-3 rounded-2xl max-w-[85%] border border-cyber-cyan/30 shadow-[0_0_15px_rgba(0,240,255,0.08)] text-[14.5px] leading-relaxed font-sans">
                {/* User Header Metadata */}
                <div className="flex items-center justify-between gap-3 text-[9px] font-mono text-zinc-500 mb-1.5 border-b border-cyber-cyan/15 pb-1 select-none">
                  <span className="text-cyber-cyan font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan" />
                    OPERATOR // DIRECT INTENT
                  </span>
                  <span>ENCRYPTED</span>
                </div>

                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {attachments.map((att, idx) => {
                      const Icon = getDocIcon(att.filename);
                      return (
                        <button
                          key={idx}
                          onClick={() => openAttachmentReader(att)}
                          className="flex items-center gap-1.5 px-2 py-1 rounded bg-black/60 hover:bg-black/90 border border-cyber-cyan/25 text-[11px] font-mono text-cyber-cyan transition-all"
                        >
                          <Icon size={12} className="text-cyber-cyan" />
                          <span>{att.filename}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
                {cleanText}
              </div>
            </div>
          );
        }

        // System/Agent message
        return (
          <div key={line.id || i} className="flex flex-col w-full animate-slide-up text-text space-y-3 relative">
            {/* Tactical Agent Message Header */}
            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 select-none px-1 border-b border-white/5 pb-1">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
                <span className="text-white font-bold tracking-wider uppercase">
                  {line.agent && line.agent !== "system" ? line.agent : "GOD'S EYE // COPPER OS"}
                </span>
                <span className="text-cyber-cyan/70">[CONFIDENCE: 98%]</span>
              </div>
              <span className="text-zinc-600">AIR-GAPPED SYNTHESIS</span>
            </div>

            {line.taskGraph && (
              <TaskGraphVisualizer graph={line.taskGraph} className="my-2" />
            )}
            {line.computerUseSteps && line.computerUseSteps.length > 0 && (
              <ComputerUseVisualizer steps={line.computerUseSteps} isLive={false} className="my-2" />
            )}
            <div className="w-full markdown-body font-sans text-[14.5px] leading-relaxed">
              <MarkdownContent content={cleanText} />
            </div>
            {line.metrics && (
              <MessageMetricsBar metrics={line.metrics} text={cleanText} />
            )}
            <AnimatePresence>
              {isLastAssistant && showCorrection && (
                <CorrectionAckPill summary={showCorrection.summary} onFade={() => setShowCorrection(null)} />
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {/* Active Live Task Graph */}
      {activeTaskGraph && (
        <div className="w-full animate-slide-up">
          <TaskGraphVisualizer graph={activeTaskGraph} />
        </div>
      )}

      {/* Active Live Computer Use Overlay */}
      {activeComputerUse && activeComputerUse.length > 0 && (
        <div className="w-full animate-slide-up">
          <ComputerUseVisualizer steps={activeComputerUse} isLive={true} />
        </div>
      )}

      {thinking && activeAgent && !activeTaskGraph && (
        <div className="flex flex-col w-full animate-slide-up text-zinc-400 space-y-3 font-mono">
          <div className="flex items-center gap-2 text-xs text-cyber-cyan">
            <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping" />
            <span className="tracking-wider uppercase">Neural Reasoning & Tool Execution Active...</span>
          </div>
          <div className="flex items-center gap-3 p-3.5 rounded-xl border border-cyber-cyan/30 bg-[#070d18]/80 backdrop-blur-xl shadow-hud">
            <div className="w-7 h-7 rounded-lg bg-cyber-cyan/15 border border-cyber-cyan/40 flex items-center justify-center flex-shrink-0">
              <Cpu size={14} className="text-cyber-cyan animate-pulse" />
            </div>
            <div className="flex flex-col">
              <span className="text-[13px] text-white font-bold font-sans">
                {agentStats[activeAgent]?.name || activeAgent}
              </span>
              <span className="text-[10.5px] text-zinc-400 font-mono">
                Executing cognitive tasks across local agent mesh...
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
