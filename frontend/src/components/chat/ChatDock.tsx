import React, { useState, useRef, useEffect } from "react";
import {
  Paperclip,
  ArrowUp,
  Mic,
  Sparkles,
  FileCode,
  X,
  ChevronUp,
  CornerDownLeft,
  Loader2,
  Eye
} from "lucide-react";
import { Brain, BookOpen, Zap } from "lucide-react";
import { API_BASE } from "../../lib/api";

interface Props {
  connected: boolean;
  thinking: boolean;
  onSend: (message: string, mode?: string) => void;
}

interface AttachedFile {
  name: string;
  size: string;
  type: string;
  content: string;
  rawPreview?: string;
  lineCount?: number;
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
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(COGNITIVE_MODES[0]);
  const [previewFile, setPreviewFile] = useState<AttachedFile | null>(null);
  
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
    if (attachedFiles.length > 0) {
      const fileBlocks = attachedFiles.map(
        (f) => `\n\n--- Attached File: ${f.name} ---\n\`\`\`\n${f.content}\n\`\`\``
      ).join("");
      fullMsg = fullMsg ? `${fullMsg}\n${fileBlocks}` : fileBlocks.trim();
    }

    if (!fullMsg || thinking || isRecording) return;

    onSend(fullMsg, selectedModel.id);
    setDraft("");
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    Array.from(files).forEach((file) => {
      const ext = file.name.split(".").pop()?.toLowerCase() || "";
      const textExtensions = [
        "txt", "csv", "tsv", "json", "py", "js", "ts", "tsx", "jsx", "html",
        "css", "sql", "md", "yaml", "yml", "xml", "log", "env", "ini", "sh",
        "bat", "ps1", "c", "cpp", "h", "hpp", "rs", "go", "java"
      ];

      const isKnownText = textExtensions.includes(ext);
      const isLarge = file.size > 50 * 1024; // > 50 KB
      const sliceSize = isLarge ? 50 * 1024 : file.size; // Read up to 50 KB
      const blob = file.slice(0, sliceSize);

      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      const sizeKb = (file.size / 1024).toFixed(1);
      const displaySize = file.size > 1024 * 1024 ? `${sizeMb} MB` : `${sizeKb} KB`;

      const reader = new FileReader();
      reader.onload = (event) => {
        let rawText = (event.target?.result as string) || "";

        // Detect unprintable binary bytes (null bytes or corrupted characters)
        const isBinary = !isKnownText && (rawText.includes("\0") || rawText.includes("\ufffd") || (rawText.match(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g)?.length || 0) > 10);

        let formattedText = "";
        let lineCount = rawText.split("\n").length;

        if (isBinary) {
          formattedText = `[Attached Document: ${file.name} (${displaySize})]\n[File Type: .${ext.toUpperCase()} Binary Document/Archive]\nNote: This file is binary encoded. For deep code/data inspection, please upload plain text, CSV, JSON, Markdown, or code files.`;
        } else if (isLarge) {
          const lines = rawText.split("\n");
          const preview = lines.slice(0, 100).join("\n");
          formattedText = `[Attached Large Dataset/File: ${file.name} (${displaySize})]\n[Structure Preview & Sample Data (First 100 lines)]:\n${preview}\n\n[... End of sample preview. Total file size: ${displaySize} ...]`;
        } else {
          formattedText = rawText;
        }

        setAttachedFiles((prev) => [
          ...prev,
          {
            name: file.name,
            size: displaySize,
            type: ext ? `.${ext.toUpperCase()}` : "FILE",
            content: formattedText,
            rawPreview: rawText,
            lineCount: lineCount
          }
        ]);
      };
      reader.readAsText(blob);
    });

    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
    if (previewFile && attachedFiles[index]?.name === previewFile.name) {
      setPreviewFile(null);
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

      {/* Interactive File Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-2xl max-h-[80vh] flex flex-col rounded-2xl bg-slate-900 border border-border shadow-2xl overflow-hidden font-mono text-xs text-slate-200">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 bg-slate-950 border-b border-border">
              <div className="flex items-center gap-2.5">
                <FileCode size={18} className="text-accent" />
                <span className="font-bold text-sm text-white">{previewFile.name}</span>
                <span className="px-2 py-0.5 rounded-full bg-accent/20 text-accent text-[10px] font-semibold">
                  {previewFile.type}
                </span>
                <span className="text-slate-400 text-[11px]">({previewFile.size})</span>
              </div>
              <button
                onClick={() => setPreviewFile(null)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Content Preview Box */}
            <div className="flex-1 p-4 overflow-y-auto custom-scrollbar bg-slate-950/60 font-mono text-xs leading-relaxed text-slate-300">
              <pre className="whitespace-pre-wrap select-text">
                {previewFile.content}
              </pre>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-5 py-3 bg-slate-950/90 border-t border-border text-[11px] text-slate-400">
              <span>Ready for local AI analysis</span>
              <button
                onClick={() => setPreviewFile(null)}
                className="px-4 py-1.5 rounded-xl bg-accent text-bg font-bold hover:bg-accent-hover transition-colors"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Attached Files Preview Chips Bar */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 px-2 animate-slide-up">
          {attachedFiles.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-900 border border-slate-800 hover:border-accent/50 text-xs font-mono text-cyan-300 shadow-sm transition-all cursor-pointer group"
              onClick={() => setPreviewFile(file)}
            >
              <FileCode size={14} className="text-accent group-hover:scale-110 transition-transform" />
              <span className="max-w-[160px] truncate group-hover:text-white transition-colors">{file.name}</span>
              <span className="text-[10px] text-text-muted">({file.size})</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setPreviewFile(file);
                }}
                className="p-0.5 hover:text-accent rounded transition-colors text-slate-400"
                title="Preview File"
              >
                <Eye size={12} />
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(idx);
                }}
                className="p-0.5 hover:bg-slate-800 rounded-full text-text-muted hover:text-rose-400 transition-colors ml-1"
                title="Remove File"
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main Glassmorphism Input Capsule */}
      <div
        className={`w-full flex flex-col rounded-2xl bg-bg-panel/90 backdrop-blur-xl border transition-all duration-300 shadow-lg ${
          thinking
            ? "border-accent shadow-neon animate-pulse-glow"
            : isRecording
            ? "border-rose-500/80 shadow-[0_0_20px_rgba(244,63,94,0.3)] bg-rose-950/10"
            : "border-border/80 focus-within:border-accent/80 hover:border-border focus-within:shadow-[0_0_20px_rgba(14,165,233,0.15)]"
        }`}
      >
        {/* Active Recording State Banner */}
        {isRecording ? (
          <div className="flex items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping" />
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-rose-400 font-mono">
                  Listening to Voice Input...
                </span>
                <span className="text-xs text-text-muted font-mono">
                  Duration: {formatTimer(recordDuration)} | Whisper STT Ready
                </span>
              </div>
            </div>

            {/* Live pulsating audio wave bars */}
            <div className="flex items-center gap-1.5 h-6">
              {[40, 70, 95, 60, 85, 50, 90, 65, 45].map((h, i) => (
                <span
                  key={i}
                  className="w-1 bg-rose-500 rounded-full animate-pulse"
                  style={{
                    height: `${h}%`,
                    animationDuration: `${0.4 + (i % 3) * 0.2}s`,
                    animationDelay: `${i * 0.08}s`
                  }}
                />
              ))}
            </div>

            <button
              onClick={stopRecording}
              className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white font-mono text-xs font-bold shadow-lg transition-all"
            >
              Finish &amp; Transcribe
            </button>
          </div>
        ) : (
          <>
            {/* Input Text Area */}
            <div className="px-4 pt-3.5 pb-1">
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
                    ? "C.O.P.P.E.R. is processing..."
                    : "Message C.O.P.P.E.R. (Enter to send, Shift+Enter for new line)..."
                }
                disabled={thinking}
                className="w-full bg-transparent outline-none border-none border-0 ring-0 shadow-none focus:outline-none focus:ring-0 focus:border-none focus-visible:outline-none focus-visible:ring-0 text-[14.5px] leading-relaxed text-text placeholder:text-text-muted/60 resize-none max-h-48 min-h-[38px] custom-scrollbar"
                rows={1}
              />
            </div>

            {/* Bottom Actions Toolbar */}
            <div className="flex items-center justify-between px-3 pb-2.5 pt-1 border-t border-white/[0.04]">
              <div className="flex items-center gap-1.5">
                {/* Model Pill Button */}
                <button
                  type="button"
                  onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-bg-raised/80 hover:bg-bg-raised border border-border/50 text-[11px] font-mono text-accent font-medium transition-all"
                >
                  <selectedModel.icon size={13} className="text-accent" />
                  <span>{selectedModel.name}</span>
                  <ChevronUp size={12} className={`transition-transform duration-200 ${modelDropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {/* File Attachment Button */}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-1.5 text-text-muted hover:text-accent hover:bg-accent/10 rounded-lg transition-all"
                  title="Attach file (.txt, .py, .js, .json, .csv, .md)"
                >
                  <Paperclip size={16} />
                </button>
              </div>

              {/* Right Side: Microphone & Send Button */}
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-text-muted/50 font-mono hidden sm:inline-flex items-center gap-1">
                  <span>Enter</span>
                  <CornerDownLeft size={10} />
                </span>

                {/* Voice Input Button */}
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={thinking}
                  className="p-2 rounded-xl text-accent hover:text-white hover:bg-accent/20 transition-all disabled:opacity-30"
                  title="Speak with Voice"
                >
                  <Mic size={17} />
                </button>

                {/* Send Button */}
                <button
                  type="button"
                  onClick={submit}
                  disabled={(!draft.trim() && attachedFiles.length === 0) || thinking}
                  className="p-2 rounded-xl bg-accent text-bg hover:bg-accent-hover hover:shadow-neon disabled:opacity-20 disabled:hover:bg-accent disabled:shadow-none transition-all duration-200 flex items-center justify-center cursor-pointer disabled:cursor-not-allowed"
                  title={connected ? "Send message" : "Reconnecting..."}
                >
                  {thinking ? (
                    <Loader2 size={16} className="animate-spin text-bg" />
                  ) : (
                    <ArrowUp size={16} strokeWidth={2.5} />
                  )}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
