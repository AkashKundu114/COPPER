import { useEffect, useRef, useState } from "react";
import { type ChatLine } from "../../hooks/useBrainSocket";
import { type AgentStats, type ParsedDocument } from "../../lib/api";
import { Bot, User, FileText, BookOpen, FileCode, Table, Braces, Eye } from "lucide-react";
import { MarkdownContent } from "./MarkdownContent";
import { DocumentReaderModal } from "../documents/DocumentReaderModal";

interface MessageFeedProps {
  lines: ChatLine[];
  agentStats: Record<string, AgentStats>;
  thinking: boolean;
  activeAgent: string | null;
}

function formatTime(ts?: number) {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
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
    
    // codeBlock might have a language tag on the first line
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
      content
    });
  }

  const cleanText = text.replace(/--- Attached File: [\s\S]*?```/g, "").trim();
  return { cleanText, attachments };
}

export function MessageFeed({
  lines,
  agentStats,
  thinking,
  activeAgent,
}: MessageFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);
  const [selectedDoc, setSelectedDoc] = useState<ParsedDocument | null>(null);

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
    const sizeFormatted = sizeBytes > 1024 * 1024 ? `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB` : `${(sizeBytes / 1024).toFixed(1)} KB`;

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
      status: "success"
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
      className="flex-1 w-full max-w-4xl mx-auto overflow-y-auto px-6 py-8 space-y-8 custom-scrollbar"
    >
      {selectedDoc && (
        <DocumentReaderModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}

      {lines.map((line, i) => {
        const isUser = line.agent === "YOU" || line.agent === "user";
        const agentName =
          line.agent && line.agent !== "YOU"
            ? agentStats[line.agent]?.name || line.agent
            : "C.O.P.P.E.R.";

        const { cleanText, attachments } = isUser ? parseAttachments(line.text) : { cleanText: line.text, attachments: [] };

        return (
          <div
            key={line.id || i}
            className={`flex gap-4 ${isUser ? "flex-row-reverse" : "flex-row"} animate-slide-up`}
          >
            <div
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? "bg-bg-raised text-text" : "bg-bg-panel border border-border text-accent"}`}
            >
              {isUser ? <User size={16} /> : <Bot size={16} />}
            </div>

            <div
              className={`flex flex-col max-w-[85%] ${isUser ? "items-end" : "items-start"}`}
            >
              <div
                className={`flex items-center gap-2 mb-1 px-1.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
              >
                <span className="text-xs text-text-muted font-medium">
                  {isUser ? "You" : agentName}
                </span>
                <span className="text-[10px] text-text-muted/60 font-mono">
                  {formatTime(line.timestamp)}
                </span>
              </div>

              <div
                className={`px-5 py-4 rounded-2xl shadow-sm ${isUser ? "bg-bg-raised text-text border border-border/50" : "bg-bg-panel border border-border text-text"}`}
              >
                {isUser ? (
                  <div className="space-y-3">
                    {/* Render Document Attachment Badges */}
                    {attachments.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-0.5">
                        {attachments.map((att, idx) => {
                          const Icon = getDocIcon(att.filename);
                          return (
                            <button
                              key={idx}
                              onClick={() => openAttachmentReader(att)}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-900 border border-slate-700/80 hover:border-sky-400/80 text-xs font-mono text-cyan-300 shadow-sm transition-all cursor-pointer group"
                              title="Click to Open Document Reader"
                            >
                              <Icon size={14} className="text-sky-400 group-hover:scale-110 transition-transform" />
                              <span className="font-bold text-white group-hover:text-sky-300 transition-colors">
                                {att.filename}
                              </span>
                              <span className="text-[10px] text-slate-400 flex items-center gap-1 ml-1 bg-slate-800 px-1.5 py-0.5 rounded">
                                <Eye size={10} />
                                <span>Preview</span>
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {cleanText && (
                      <p className="whitespace-pre-wrap leading-relaxed text-sm">
                        {cleanText}
                      </p>
                    )}
                  </div>
                ) : (
                  <MarkdownContent content={line.text} />
                )}
              </div>
            </div>
          </div>
        );
      })}

      {thinking && activeAgent && (
        <div className="flex gap-4 flex-row animate-slide-up">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-bg-panel border border-border text-accent flex items-center justify-center">
            <Bot size={16} className="animate-pulse" />
          </div>
          <div className="flex flex-col max-w-[80%] items-start">
            <span className="text-xs text-text-muted mb-1 font-medium px-1">
              {agentStats[activeAgent]?.name || activeAgent}
            </span>
            <div className="px-4 py-3 rounded-2xl bg-bg-panel border border-border text-text flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: "0ms" }}></span>
              <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: "150ms" }}></span>
              <span className="w-2 h-2 rounded-full bg-text-muted animate-bounce" style={{ animationDelay: "300ms" }}></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
