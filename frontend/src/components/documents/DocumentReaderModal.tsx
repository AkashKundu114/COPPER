import React, { useState, useMemo, useEffect } from "react";
import {
  X,
  FileText,
  FileCode,
  Table,
  Braces,
  Copy,
  Check,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BookOpen,
  Eye,
  ListFilter
} from "lucide-react";
import { type ParsedDocument } from "../../lib/api";

interface Props {
  document: ParsedDocument;
  onClose: () => void;
  onAskAI?: (prompt: string) => void;
}

export const DocumentReaderModal: React.FC<Props> = ({ document, onClose, onAskAI }) => {
  const [activeTab, setActiveTab] = useState<"reader" | "search" | "analytics" | "raw">("reader");
  const [selectedPage, setSelectedPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const ext = document.extension.toLowerCase();
  const isPdf = ext === "pdf";
  const isTable = ext === "csv" || ext === "tsv";
  const isJson = ext === "json";
  const isCode = [
    "py", "js", "ts", "tsx", "jsx", "html", "css", "sql", "rs", "go",
    "java", "c", "cpp", "h", "hpp", "sh", "bat", "ps1", "yaml", "yml", "xml"
  ].includes(ext);

  // Pick Document Icon
  const DocIcon = useMemo(() => {
    if (isPdf) return BookOpen;
    if (isTable) return Table;
    if (isJson) return Braces;
    if (isCode) return FileCode;
    return FileText;
  }, [isPdf, isTable, isJson, isCode]);

  const handleCopy = () => {
    navigator.clipboard.writeText(document.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([document.full_text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = document.filename.endsWith(".txt") ? document.filename : `${document.filename}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSummarizeWithAI = () => {
    if (onAskAI) {
      onAskAI(
        `Please analyze and provide a comprehensive, structured summary of the attached document: "${document.filename}". Highlight core objectives, key findings, data tables, and actionable insights.`
      );
      onClose();
    }
  };

  // Search Results inside document
  const searchMatches = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const query = searchQuery.toLowerCase();
    const lines = document.full_text.split("\n");
    const matches: { lineNumber: number; text: string }[] = [];

    lines.forEach((line, idx) => {
      if (line.toLowerCase().includes(query)) {
        matches.push({ lineNumber: idx + 1, text: line });
      }
    });
    return matches;
  }, [searchQuery, document.full_text]);

  const activePageContent = useMemo(() => {
    if (!isPdf || document.pages.length === 0) return document.full_text;
    const page = document.pages.find((p) => p.page_number === selectedPage);
    return page ? page.text : document.pages[0]?.text || "";
  }, [isPdf, document.pages, selectedPage]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-5xl h-[88vh] flex flex-col rounded-3xl bg-slate-900/95 border border-slate-700/80 shadow-2xl overflow-hidden font-sans text-slate-200">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center gap-3 min-w-0">
            <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/30 flex-shrink-0">
              <DocIcon size={22} className="text-sky-400" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-base text-white tracking-tight truncate max-w-md" title={document.filename}>
                  {document.filename}
                </h2>
                <span className="px-2 py-0.5 rounded-md bg-sky-950 text-sky-400 border border-sky-800/50 text-[10px] font-mono font-bold uppercase">
                  {document.extension || "DOC"}
                </span>
                {document.indexed_chunks > 0 && (
                  <span className="hidden sm:inline-flex px-2 py-0.5 rounded-md bg-emerald-950 text-emerald-400 border border-emerald-800/50 text-[10px] font-mono">
                    AI Indexed ({document.indexed_chunks} chunks)
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {document.category} · {document.size_formatted} · {document.word_count.toLocaleString()} words · ~{document.estimated_tokens.toLocaleString()} tokens
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onAskAI && (
              <button
                onClick={handleSummarizeWithAI}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-slate-950 font-bold text-xs shadow-md shadow-sky-500/20 transition-all cursor-pointer"
                title="Ask C.O.P.P.E.R. to summarize this document"
              >
                <Sparkles size={14} />
                <span>Analyze with AI</span>
              </button>
            )}

            <button
              onClick={handleCopy}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Copy Document Text"
            >
              {copied ? <Check size={16} className="text-emerald-400" /> : <Copy size={16} />}
            </button>

            <button
              onClick={handleDownload}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              title="Download Extracted Text"
            >
              <Download size={16} />
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors ml-1"
              title="Close Reader (Esc)"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Tab Navigation Toolbar */}
        <div className="flex items-center justify-between px-6 py-2 bg-slate-950/60 border-b border-slate-800/80 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setActiveTab("reader")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "reader"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Eye size={13} />
              <span>Interactive Reader</span>
            </button>

            <button
              onClick={() => setActiveTab("search")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "search"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <Search size={13} />
              <span>Search in Doc {searchMatches.length > 0 && `(${searchMatches.length})`}</span>
            </button>

            <button
              onClick={() => setActiveTab("analytics")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "analytics"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <ListFilter size={13} />
              <span>Doc Analytics</span>
            </button>

            <button
              onClick={() => setActiveTab("raw")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                activeTab === "raw"
                  ? "bg-sky-500/20 text-sky-400 border border-sky-500/40 font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <FileText size={13} />
              <span>Raw Text</span>
            </button>
          </div>

          {/* PDF Page Controls */}
          {isPdf && document.pages.length > 1 && activeTab === "reader" && (
            <div className="flex items-center gap-2 text-slate-300">
              <button
                onClick={() => setSelectedPage((p) => Math.max(1, p - 1))}
                disabled={selectedPage === 1}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30"
              >
                <ChevronLeft size={15} />
              </button>
              <span>
                Page <strong className="text-white">{selectedPage}</strong> of {document.pages.length}
              </span>
              <button
                onClick={() => setSelectedPage((p) => Math.min(document.pages.length, p + 1))}
                disabled={selectedPage === document.pages.length}
                className="p-1 rounded hover:bg-slate-800 disabled:opacity-30"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          )}
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-slate-950/40">
          {/* TAB 1: INTERACTIVE READER */}
          {activeTab === "reader" && (
            <div className="max-w-4xl mx-auto space-y-4">
              {/* CSV / Tabular Viewer */}
              {isTable && document.structured_data?.headers && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-lg">
                  <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
                    <span>
                      Table: {document.structured_data.total_rows} rows · {document.structured_data.column_count} columns
                    </span>
                    <span className="text-sky-400">Showing first 50 rows</span>
                  </div>
                  <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-left text-xs font-mono border-collapse">
                      <thead>
                        <tr className="bg-slate-800/80 text-sky-300 border-b border-slate-700">
                          {document.structured_data.headers.map((h: string, idx: number) => (
                            <th key={idx} className="p-3 font-semibold whitespace-nowrap">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {document.structured_data.preview_rows?.map((row: string[], rIdx: number) => (
                          <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                            {row.map((cell: string, cIdx: number) => (
                              <td key={cIdx} className="p-3 whitespace-nowrap">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* PDF Document Page View */}
              {isPdf && (
                <div className="p-8 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4 font-serif text-[14.5px] leading-relaxed text-slate-200">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800 font-sans text-xs font-mono text-slate-400">
                    <span className="text-sky-400 font-bold uppercase">Page {selectedPage} of {document.pages.length}</span>
                    <span>{document.pages[selectedPage - 1]?.word_count || 0} words on page</span>
                  </div>
                  <div className="whitespace-pre-wrap select-text font-mono text-xs leading-relaxed">
                    {activePageContent || "(No readable text detected on this page)"}
                  </div>
                </div>
              )}

              {/* Code / Markdown / Text Line Gutter View */}
              {!isTable && !isPdf && (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-xl overflow-hidden font-mono text-xs">
                  <div className="flex items-center justify-between px-4 py-2 bg-slate-950 border-b border-slate-800 text-[11px] text-slate-400">
                    <span className="uppercase text-sky-400 font-bold">{document.extension} Document View</span>
                    <span>{document.line_count} total lines</span>
                  </div>
                  <div className="p-4 flex gap-4 overflow-x-auto custom-scrollbar select-text leading-relaxed">
                    {/* Line numbers gutter */}
                    <div className="text-slate-600 select-none text-right pr-3 border-r border-slate-800 font-mono">
                      {document.full_text.split("\n").map((_, i) => (
                        <div key={i}>{i + 1}</div>
                      ))}
                    </div>
                    {/* Source content */}
                    <pre className="text-slate-200 flex-1 whitespace-pre">
                      {document.full_text}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: IN-DOCUMENT SEARCH */}
          {activeTab === "search" && (
            <div className="max-w-3xl mx-auto space-y-4 font-mono text-xs">
              <div className="relative">
                <Search size={16} className="absolute left-3.5 top-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search keywords or phrases in document..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-2xl bg-slate-900 border border-slate-800 text-white outline-none focus:border-sky-500 text-sm shadow-inner"
                  autoFocus
                />
              </div>

              {searchQuery.trim() && (
                <div className="text-xs text-slate-400 px-1">
                  Found <strong className="text-sky-400">{searchMatches.length}</strong> matching lines:
                </div>
              )}

              <div className="space-y-2">
                {searchMatches.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 bg-slate-900/40 rounded-2xl border border-slate-800">
                    {searchQuery.trim() ? "No matching occurrences found." : "Type a query above to search inside this document."}
                  </div>
                ) : (
                  searchMatches.map((m, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-sky-500/40 flex items-start gap-3 transition-colors"
                    >
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-400 text-[11px] font-bold">
                        L{m.lineNumber}
                      </span>
                      <p className="text-slate-200 select-text flex-1 whitespace-pre-wrap">
                        {m.text}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: DOCUMENT ANALYTICS */}
          {activeTab === "analytics" && (
            <div className="max-w-3xl mx-auto space-y-6 font-mono text-xs">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400 uppercase">Words</div>
                  <div className="text-xl font-bold text-white font-sans">{document.word_count.toLocaleString()}</div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400 uppercase">Characters</div>
                  <div className="text-xl font-bold text-sky-400 font-sans">{document.char_count.toLocaleString()}</div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400 uppercase">Lines / Pages</div>
                  <div className="text-xl font-bold text-purple-400 font-sans">
                    {document.page_count > 1 ? `${document.page_count} Pages` : `${document.line_count} Lines`}
                  </div>
                </div>
                <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1">
                  <div className="text-[11px] text-slate-400 uppercase">Est. Tokens</div>
                  <div className="text-xl font-bold text-emerald-400 font-sans">{document.estimated_tokens.toLocaleString()}</div>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                <h3 className="font-bold text-sm text-white font-sans flex items-center gap-2">
                  <Sparkles size={16} className="text-sky-400" />
                  <span>Document Metadata & AI Ingestion</span>
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">FILE NAME</span>
                    <span className="text-white font-bold">{document.filename}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">CATEGORY</span>
                    <span className="text-sky-400 font-bold">{document.category}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">FILE SIZE</span>
                    <span className="text-white font-bold">{document.size_formatted} ({document.size_bytes.toLocaleString()} bytes)</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">CHROMA RAG INDEX</span>
                    <span className="text-emerald-400 font-bold">
                      {document.indexed_chunks > 0 ? `Ready (${document.indexed_chunks} chunks)` : "Not indexed"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: RAW SOURCE */}
          {activeTab === "raw" && (
            <div className="max-w-4xl mx-auto rounded-2xl bg-slate-900/90 border border-slate-800 p-5 font-mono text-xs text-slate-200 select-text overflow-x-auto custom-scrollbar leading-relaxed">
              <pre className="whitespace-pre-wrap">{document.full_text}</pre>
            </div>
          )}
        </div>

        {/* Footer Bar */}
        <div className="flex items-center justify-between px-6 py-3 bg-slate-950 border-t border-slate-800 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Document Parsed & Ready for C.O.P.P.E.R. Execution</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold transition-colors cursor-pointer"
          >
            Close Reader
          </button>
        </div>
      </div>
    </div>
  );
};
