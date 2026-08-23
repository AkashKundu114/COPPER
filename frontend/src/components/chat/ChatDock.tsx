import React, { useState, useRef, useEffect } from "react";
import {
  Paperclip,
  ArrowUp,
  Mic,
  Sparkles,
  FileCode,
  FileText,
  Table,
  Braces,
  BookOpen,
  X,
  ChevronUp,
  CornerDownLeft,
  Loader2,
  Eye,
  Brain,
  Zap
} from "lucide-react";
import { API_BASE, parseDocumentFile, type ParsedDocument } from "../../lib/api";
import { DocumentReaderModal } from "../documents/DocumentReaderModal";

interface Props {
  connected: boolean;
  thinking: boolean;
  onSend: (message: string, mode?: string) => void;
}

export interface AttachedDocState {
  file: File;
  parsed: ParsedDocument;
  isParsing?: boolean;
}

const COGNITIVE_MODES = [
  {
    id: "auto",
    name: "Adaptive Intent",
    badge: "Autonomous",
    icon: Sparkles,
    desc: "Autonomous Guardian router dynamically coordinating all 30 local agent specialists.",
    agents: "Guardian · Master Router · Dispatcher"
  },
  {
    id: "reasoning",
    name: "Deep Cognitive",
    badge: "Complex & Thinking",
    icon: Brain,
    desc: "Chain-of-thought with live collapsible thinking breakdown for complex logic, math, & strategy.",
    agents: "Cognitive Reasoner · Logic Validator · Solver"
  },
  {
    id: "coding",
    name: "Software Architect",
    badge: "Code & Dev",
    icon: FileCode,
    desc: "Full-stack code synthesis, multi-file architecture, edge-case testing, and syntax optimization.",
    agents: "Code Engineer · Refactor Specialist · Auditor"
  },
  {
    id: "research",
    name: "Deep Research",
    badge: "Synthesis Tier",
    icon: BookOpen,
    desc: "Epistemic fact-checking, document decomposition, cross-analysis, and evidence generation.",
    agents: "Document Analyst · Fact Synthesizer"
  },
  {
    id: "fast",
    name: "Instant Reflex",
    badge: "Speed Tier",
    icon: Zap,
    desc: "Zero-latency, direct, concise responses with minimal compute overhead.",
    agents: "Fast Responder · Executive Assistant"
  }
];

export function ChatDock({ connected, thinking, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [attachedDocs, setAttachedDocs] = useState<AttachedDocState[]>([]);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(COGNITIVE_MODES[0]);
  const [previewDoc, setPreviewDoc] = useState<ParsedDocument | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const recordTimerRef = useRef<number | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 180)}px`;
    }
  }, [draft]);

  // Recording duration timer
  useEffect(() => {
    if (isRecording) {
      setRecordDuration(0);
      recordTimerRef.current = window.setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (recordTimerRef.current) clearInterval(recordTimerRef.current);
      setRecordDuration(0);
    }
    return () => {
      if (recordTimerRef.current) clearInterval(recordTimerRef.current);
    };
  }, [isRecording]);

  const submit = () => {
    let fullMsg = draft.trim();
    if (attachedDocs.length > 0) {
      const fileBlocks = attachedDocs.map((doc) => {
        const p = doc.parsed;
        return `\n\n--- Attached File: ${p.filename} (${p.category}, ${p.size_formatted}) ---\n\`\`\`${p.extension || "text"}\n${p.full_text}\n\`\`\``;
      }).join("");
      fullMsg = fullMsg ? `${fullMsg}\n${fileBlocks}` : fileBlocks.trim();
    }

    if (!fullMsg || thinking || isRecording || isUploading) return;

    onSend(fullMsg, selectedModel.id);
    setDraft("");
    setAttachedDocs([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    const newDocPromises = Array.from(files).map(async (file): Promise<AttachedDocState> => {
      try {
        const parsed = await parseDocumentFile(file, true);
        return { file, parsed, isParsing: false };
      } catch (err) {
        console.warn("Backend parsing error, creating client document fallback:", err);
        const ext = file.name.split(".").pop()?.toLowerCase() || "";
        const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
        const sizeKb = (file.size / 1024).toFixed(1);
        const size_formatted = file.size > 1024 * 1024 ? `${sizeMb} MB` : `${sizeKb} KB`;

        let rawText = "";
        try {
          rawText = await file.text();
        } catch {
          rawText = `[Binary / Document File: ${file.name}]`;
        }

        const lines = rawText.split("\n");
        const fallbackParsed: ParsedDocument = {
          filename: file.name,
          extension: ext,
          category: ext.toUpperCase() + " Document",
          size_bytes: file.size,
          size_formatted,
          page_count: 1,
          line_count: lines.length,
          word_count: rawText.split(/\s+/).filter(Boolean).length,
          char_count: rawText.length,
          estimated_tokens: Math.max(1, Math.floor(rawText.length / 4)),
          indexed_chunks: 0,
          pages: [{ page_number: 1, text: rawText, word_count: rawText.split(/\s+/).filter(Boolean).length, char_count: rawText.length }],
          full_text: rawText,
          preview_text: rawText.slice(0, 500),
          status: "partial"
        };
        return { file, parsed: fallbackParsed, isParsing: false };
      }
    });

    try {
      const results = await Promise.all(newDocPromises);
      setAttachedDocs((prev) => [...prev, ...results]);
    } catch (error) {
      console.error("File upload error:", error);
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const removeFile = (index: number) => {
    setAttachedDocs((prev) => prev.filter((_, i) => i !== index));
    if (previewDoc && attachedDocs[index]?.parsed.filename === previewDoc.filename) {
      setPreviewDoc(null);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());

        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");

        try {
          const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            onSend(data.text);
          }
        } catch (e) {
          console.error("Voice transcription error", e);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (e) {
      console.error("Mic access denied", e);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const getDocIcon = (ext: string) => {
    if (ext === "pdf") return BookOpen;
    if (ext === "csv" || ext === "tsv") return Table;
    if (ext === "json") return Braces;
    if (["py", "js", "ts", "tsx", "jsx", "html", "css", "sql", "rs", "go", "java", "c", "cpp"].includes(ext)) {
      return FileCode;
    }
    return FileText;
  };

  return (
    <div className="w-full relative flex flex-col gap-2 select-none">
      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileUpload}
      />

      {/* Cognitive Intelligence Mode Selector Popover */}
      {modelDropdownOpen && (
        <div className="absolute bottom-full mb-2 left-0 w-80 sm:w-96 rounded-2xl bg-slate-900/95 backdrop-blur-xl border border-slate-800 shadow-2xl p-2.5 z-50 animate-slide-up font-mono text-xs">
          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800 flex items-center justify-between">
            <span>Cognitive Intelligence Mode</span>
            <span className="text-sky-400">5 Active Squads</span>
          </div>
          <div className="space-y-1.5 mt-2 max-h-80 overflow-y-auto custom-scrollbar">
            {COGNITIVE_MODES.map((m) => {
              const Icon = m.icon;
              const isSelected = selectedModel.id === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => {
                    setSelectedModel(m);
                    setModelDropdownOpen(false);
                  }}
                  className={`w-full flex items-start gap-3 p-2.5 rounded-xl text-left transition-all ${
                    isSelected
                      ? "bg-sky-500/15 text-sky-400 border border-sky-500/40 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 border border-transparent"
                  }`}
                >
                  <div className={`p-1.5 rounded-lg mt-0.5 ${isSelected ? "bg-sky-500/20 text-sky-400" : "bg-slate-800 text-slate-400"}`}>
                    <Icon size={16} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[12px] text-white font-sans">{m.name}</span>
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-semibold uppercase ${
                        m.id === "reasoning" ? "bg-purple-950 text-purple-400 border border-purple-800/40" :
                        m.id === "coding" ? "bg-emerald-950 text-emerald-400 border border-emerald-800/40" :
                        m.id === "research" ? "bg-amber-950 text-amber-400 border border-amber-800/40" :
                        m.id === "fast" ? "bg-rose-950 text-rose-400 border border-rose-800/40" :
                        "bg-sky-950 text-sky-400 border border-sky-800/40"
                      }`}>
                        {m.badge}
                      </span>
                    </div>
                    <div className="text-[10.5px] text-slate-400 mt-0.5 leading-snug">{m.desc}</div>
                    <div className="text-[9.5px] text-slate-500 mt-1 font-mono">
                      Subagents: <span className="text-slate-300">{m.agents}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Interactive Full Document Reader & Inspector Modal */}
      {previewDoc && (
        <DocumentReaderModal
          document={previewDoc}
          onClose={() => setPreviewDoc(null)}
          onAskAI={(prompt) => {
            setPreviewDoc(null);
            onSend(prompt, selectedModel.id);
          }}
        />
      )}

      {/* Attached Files & Documents Chips Bar */}
      {(attachedDocs.length > 0 || isUploading) && (
        <div className="flex flex-wrap items-center gap-2 px-2 animate-slide-up">
          {attachedDocs.map((doc, idx) => {
            const Icon = getDocIcon(doc.parsed.extension);
            return (
              <div
                key={idx}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-900 border border-slate-800 hover:border-sky-500/50 text-xs font-mono text-cyan-300 shadow-sm transition-all cursor-pointer group"
                onClick={() => setPreviewDoc(doc.parsed)}
                title="Click to Open Document Reader & Preview"
              >
                <Icon size={14} className="text-sky-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                <span className="max-w-[160px] truncate group-hover:text-white transition-colors font-medium">
                  {doc.parsed.filename}
                </span>
                <span className="text-[10px] text-slate-400">({doc.parsed.size_formatted})</span>
                {doc.parsed.page_count > 1 && (
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800/40">
                    {doc.parsed.page_count}p
                  </span>
                )}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setPreviewDoc(doc.parsed);
                  }}
                  className="p-1 hover:bg-slate-800 hover:text-sky-400 rounded-lg text-slate-400 transition-colors ml-0.5"
                  title="Open Document Reader"
                >
                  <Eye size={13} />
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="p-0.5 hover:bg-slate-800 rounded-full text-slate-500 hover:text-rose-400 transition-colors"
                  title="Remove Document"
                >
                  <X size={13} />
                </button>
              </div>
            );
          })}

          {isUploading && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-sky-950/40 border border-sky-500/40 text-xs font-mono text-sky-400 animate-pulse">
              <Loader2 size={13} className="animate-spin" />
              <span>Parsing document & extracting text...</span>
            </div>
          )}
        </div>
      )}

      {/* Main Antigravity-Style Input Capsule */}
      <div className="w-full flex flex-col items-center">
        <div
          className={`w-full flex flex-row items-end rounded-3xl bg-[#212121] transition-all duration-300 shadow-sm border border-white/5 py-1 px-2 ${
            thinking
              ? "border-sky-500/30"
              : "focus-within:border-white/10"
          }`}
        >
          {isRecording ? (
            <div className="flex items-center justify-between w-full px-5 py-3 h-[52px]">
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
                <span className="text-sm font-semibold text-rose-400 font-mono">
                  Listening... {formatTimer(recordDuration)}
                </span>
              </div>
              <button
                onClick={stopRecording}
                className="w-8 h-8 flex items-center justify-center rounded-lg bg-rose-500 hover:bg-rose-600 text-white transition-all"
              >
                <div className="w-3 h-3 bg-white rounded-sm" />
              </button>
            </div>
          ) : (
            <>
              {/* Plus Button */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || thinking}
                className="p-2 mb-1 rounded-full text-zinc-400 hover:text-white transition-all flex-shrink-0"
                title="Attach Documents"
              >
                {isUploading ? (
                  <Loader2 size={20} className="animate-spin text-zinc-400" />
                ) : (
                  <div className="w-5 h-5 flex items-center justify-center text-xl font-light pb-1">+</div>
                )}
              </button>

              {/* Input Text Area */}
              <div className="flex-1 py-3 px-2">
                <textarea
                  ref={textareaRef}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      submit();
                    }
                  }}
                  placeholder={
                    thinking
                      ? "Thinking..."
                      : isUploading
                      ? "Uploading..."
                      : "Ask anything, @ to mention, / for actions"
                  }
                  disabled={thinking || isUploading}
                  className="w-full bg-transparent outline-none border-none text-[15px] leading-relaxed text-[#e2e2e2] placeholder:text-zinc-500 resize-none max-h-48 min-h-[24px] custom-scrollbar block"
                  rows={1}
                />
              </div>

              {/* Right Side Buttons */}
              <div className="flex items-center gap-1 mb-1.5 pr-1">
                {!draft.trim() && attachedDocs.length === 0 && !thinking && (
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className="p-2 rounded-full text-zinc-400 hover:text-white transition-all"
                  >
                    <Mic size={18} />
                  </button>
                )}

                {(draft.trim() || attachedDocs.length > 0) && !thinking && (
                  <button
                    type="button"
                    onClick={submit}
                    disabled={isUploading}
                    className="w-8 h-8 rounded-full bg-white text-black hover:bg-zinc-200 transition-all flex items-center justify-center disabled:opacity-50"
                  >
                    <ArrowUp size={18} strokeWidth={2.5} />
                  </button>
                )}

                {thinking && (
                  <button
                    type="button"
                    className="w-8 h-8 rounded-full bg-[#3f3f3f] text-rose-400 hover:bg-[#4f4f4f] hover:text-rose-300 transition-all flex items-center justify-center"
                    title="Stop generation"
                  >
                    <div className="w-3 h-3 bg-rose-400 rounded-sm" />
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Bottom Model Selector Pill */}
        <div className="flex w-full justify-start mt-3 px-2">
           <button
             type="button"
             onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
             className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-white/5 text-[12px] text-zinc-400 transition-all"
           >
             <span className="font-light">+</span>
             <span className="font-medium">{selectedModel.name}</span>
             <ChevronUp size={14} className={`transition-transform duration-200 ${modelDropdownOpen ? "rotate-180" : ""}`} />
           </button>
        </div>
      </div>
    </div>
  );
}
