import { useEffect, useRef, useState } from "react";
import { type ChatLine } from "../../hooks/useBrainSocket";
import { type AgentStats, type ParsedDocument } from "../../lib/api";
import { FileText, BookOpen, FileCode, Table, Braces, Check, Wrench, ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { MarkdownContent } from "./MarkdownContent";
import { DocumentReaderModal } from "../documents/DocumentReaderModal";

interface MessageFeedProps {
  lines: ChatLine[];
  agentStats: Record<string, AgentStats>;
  thinking: boolean;
  activeAgent: string | null;
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

function ToolCallCard({ rawCall }: { rawCall: string }) {
  const [open, setOpen] = useState(false);
  let toolName = "Tool Execution";
  let args = "";
  try {
    const parsed = JSON.parse(rawCall);
    toolName = parsed.tool || parsed.name || "Tool";
    args = JSON.stringify(parsed.arguments || {}, null, 2);
  } catch {
    args = rawCall;
  }

  return (
    <div className="my-2 rounded-xl border border-cyan-900/40 bg-cyan-950/20 text-xs font-mono overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 bg-cyan-950/40 hover:bg-cyan-950/60 text-cyan-300 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Wrench size={13} className="text-cyan-400" />
          <span className="font-bold">Tool Call: {toolName}</span>
        </div>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && (
        <pre className="p-3 text-[11px] text-cyan-200 bg-black/40 overflow-x-auto whitespace-pre-wrap">
          {args}
        </pre>
      )}
    </div>
  );
}

export function MessageFeed({
  lines,
  agentStats,
  thinking,
  activeAgent,
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
  }, [lines, thinking]);

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
              <div className="bg-white/10 backdrop-blur-md text-text px-4 py-3 rounded-2xl max-w-[85%] border border-border shadow-sm text-[15px] font-light leading-relaxed">
                {attachments.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {attachments.map((att, idx) => {
                      const Icon = getDocIcon(att.filename);
                      return (
                        <button
                          key={idx}
                          onClick={() => openAttachmentReader(att)}
                          className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#333] hover:bg-[#444] text-[11px] font-mono transition-all"
                        >
                          <Icon size={12} className="text-zinc-400" />
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
          <div key={line.id || i} className="flex flex-col w-full animate-slide-up text-text">
            <div className="w-full markdown-body">
              <MarkdownContent content={cleanText} />
            </div>
            <AnimatePresence>
              {isLastAssistant && showCorrection && (
                <CorrectionAckPill summary={showCorrection.summary} onFade={() => setShowCorrection(null)} />
              )}
            </AnimatePresence>
          </div>
        );
      })}

      {thinking && activeAgent && (
        <div className="flex flex-col w-full animate-slide-up text-zinc-400 space-y-4">
          <div className="flex items-center gap-2 text-sm">
            <span>Thought process active...</span>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl border border-border bg-white/5 backdrop-blur-md">
            <div className="w-4 h-4 rounded-full border border-zinc-600 flex items-center justify-center">
              <div className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-pulse" />
            </div>
            <div className="flex flex-col">
              <span className="text-[13px] text-white">
                {agentStats[activeAgent]?.name || activeAgent}
              </span>
              <span className="text-[11px] text-zinc-500">
                Executing tool-use and subagent tasks...
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
