import React, { useState, useEffect } from "react";
import { Check, Copy, ChevronDown, ChevronRight, Brain } from "lucide-react";

interface Props {
  content: string;
}

export const MarkdownContent: React.FC<Props> = ({ content }) => {
  // Extract <think>...</think> if present
  const { thinkContent, mainContent, isThinkingStreaming } = React.useMemo(() => {
    let think = "";
    let main = content;
    let streaming = false;

    const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/i);
    if (thinkMatch) {
      think = thinkMatch[1].trim();
      main = content.replace(/<think>[\s\S]*?<\/think>/i, "").trim();
    } else if (content.includes("<think>")) {
      const parts = content.split("<think>");
      think = parts[1]?.trim() || "";
      main = "";
      streaming = true;
    }

    return { thinkContent: think, mainContent: main, isThinkingStreaming: streaming };
  }, [content]);

  const blocks = React.useMemo(() => {
    const rawBlocks: {
      type: "code" | "heading" | "list" | "paragraph";
      lang?: string;
      text: string;
      items?: string[];
      level?: number;
    }[] = [];

    const lines = mainContent.split("\n");
    let inCode = false;
    let codeLang = "";
    let codeBuffer: string[] = [];
    let currentList: string[] = [];
    let currentParagraph: string[] = [];

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        rawBlocks.push({ type: "paragraph", text: currentParagraph.join("\n") });
        currentParagraph = [];
      }
    };

    const flushList = () => {
      if (currentList.length > 0) {
        rawBlocks.push({ type: "list", items: [...currentList], text: "" });
        currentList = [];
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith("```")) {
        if (inCode) {
          rawBlocks.push({ type: "code", lang: codeLang, text: codeBuffer.join("\n") });
          codeBuffer = [];
          codeLang = "";
          inCode = false;
        } else {
          flushParagraph();
          flushList();
          inCode = true;
          codeLang = trimmed.slice(3).trim();
        }
        continue;
      }

      if (inCode) {
        codeBuffer.push(line);
        continue;
      }

      if (!trimmed) {
        flushParagraph();
        flushList();
        continue;
      }

      if (trimmed.startsWith("#")) {
        flushParagraph();
        flushList();
        const level = trimmed.match(/^#+/)?.[0].length || 1;
        const text = trimmed.replace(/^#+\s*/, "");
        rawBlocks.push({ type: "heading", level, text });
        continue;
      }

      if (trimmed.match(/^(\*|-|\d+\.)\s+/)) {
        flushParagraph();
        const itemText = trimmed.replace(/^(\*|-|\d+\.)\s+/, "");
        currentList.push(itemText);
        continue;
      }

      flushList();
      currentParagraph.push(line);
    }

    if (inCode) {
      rawBlocks.push({ type: "code", lang: codeLang, text: codeBuffer.join("\n") });
    }
    flushParagraph();
    flushList();

    return rawBlocks;
  }, [mainContent]);

  const renderInline = (text: string) => {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      const boldItalicMatch = remaining.match(/^\*\*\*(.*?)\*\*\*/);
      if (boldItalicMatch) {
        parts.push(<strong key={key++} className="font-bold italic text-accent">{boldItalicMatch[1]}</strong>);
        remaining = remaining.slice(boldItalicMatch[0].length);
        continue;
      }

      const boldMatch = remaining.match(/^\*\*(.*?)\*\*/);
      if (boldMatch) {
        parts.push(<strong key={key++} className="font-semibold text-white">{boldMatch[1]}</strong>);
        remaining = remaining.slice(boldMatch[0].length);
        continue;
      }

      const codeMatch = remaining.match(/^`([^`]+)`/);
      if (codeMatch) {
        parts.push(
          <code key={key++} className="px-1.5 py-0.5 rounded bg-slate-900 text-cyan-300 font-mono text-xs border border-slate-700/60">
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.slice(codeMatch[0].length);
        continue;
      }

      const italicMatch = remaining.match(/^(\*|_)(.*?)\1/);
      if (italicMatch) {
        parts.push(<em key={key++} className="italic text-slate-300">{italicMatch[2]}</em>);
        remaining = remaining.slice(italicMatch[0].length);
        continue;
      }

      const nextSpecial = remaining.search(/(\*\*\*|\*\*|`|\*|_)/);
      if (nextSpecial === -1) {
        parts.push(remaining);
        break;
      } else if (nextSpecial === 0) {
        parts.push(remaining[0]);
        remaining = remaining.slice(1);
      } else {
        parts.push(remaining.slice(0, nextSpecial));
        remaining = remaining.slice(nextSpecial);
      }
    }

    return parts;
  };

  return (
    <div className="space-y-3 text-sm leading-relaxed select-text">
      {/* Claude / DeepSeek Style Collapsible Thinking Block */}
      {thinkContent && (
        <ThinkingProcessBlock
          thought={thinkContent}
          isStreaming={isThinkingStreaming}
        />
      )}

      {/* Main Formatted Markdown Blocks */}
      {blocks.map((block, i) => {
        if (block.type === "heading") {
          if (block.level === 1) return <h1 key={i} className="text-base font-bold text-white tracking-tight border-b border-border/40 pb-1 mt-2">{renderInline(block.text)}</h1>;
          if (block.level === 2) return <h2 key={i} className="text-sm font-bold text-white tracking-tight mt-2">{renderInline(block.text)}</h2>;
          return <h3 key={i} className="text-xs font-semibold text-accent mt-1">{renderInline(block.text)}</h3>;
        }

        if (block.type === "list") {
          return (
            <ul key={i} className="space-y-1.5 pl-2 my-2">
              {block.items?.map((item, j) => (
                <li key={j} className="flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0 shadow-[0_0_6px_rgba(14,165,233,0.6)]" />
                  <span className="flex-1 text-slate-200">{renderInline(item)}</span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === "code") {
          return <CodeBlock key={i} code={block.text} lang={block.lang} />;
        }

        return (
          <p key={i} className="text-slate-200 whitespace-pre-wrap">
            {renderInline(block.text)}
          </p>
        );
      })}
    </div>
  );
};

const ThinkingProcessBlock: React.FC<{ thought: string; isStreaming: boolean }> = ({ thought, isStreaming }) => {
  const [expanded, setExpanded] = useState(isStreaming);
  const [copied, setCopied] = useState(false);
  const [seconds, setSeconds] = useState(1);

  useEffect(() => {
    let timer: number | undefined;
    if (isStreaming) {
      setExpanded(true);
      timer = window.setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isStreaming]);

  const copyThought = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(thought);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const wordCount = thought.split(/\s+/).filter(Boolean).length;

  return (
    <div className={`rounded-xl overflow-hidden border shadow-sm mb-3.5 font-mono text-xs transition-all ${
      isStreaming
        ? "bg-slate-950/80 border-sky-500/50 shadow-[0_0_15px_rgba(14,165,233,0.15)]"
        : "bg-slate-950/60 border-slate-800/80"
    }`}>
      <div
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-slate-900/70 hover:bg-slate-900 border-b border-slate-800/50 text-slate-400 hover:text-slate-200 transition-all cursor-pointer select-none"
      >
        <div className="flex items-center gap-2.5">
          <div className="p-1 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <Brain size={14} className={isStreaming ? "animate-pulse text-sky-400" : "text-sky-400"} />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-[11.5px] text-slate-200">
              {isStreaming ? `Thinking (${seconds}s)...` : "Thinking Process"}
            </span>
            <span className="text-[10px] text-slate-500 font-normal">
              {wordCount} words
            </span>
          </div>
          <div className="hidden sm:flex items-center gap-1 ml-2">
            <span className="px-1.5 py-0.2 rounded bg-sky-950 text-sky-400 border border-sky-800/40 text-[9.5px]">
              Cognitive Reasoner
            </span>
            <span className="px-1.5 py-0.2 rounded bg-purple-950 text-purple-400 border border-purple-800/40 text-[9.5px]">
              Logic Validator
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <button
            type="button"
            onClick={copyThought}
            className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-200 transition-colors"
            title="Copy thought steps"
          >
            {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          </button>
          <span>{expanded ? "Hide" : "Show"}</span>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
      </div>

      {expanded && (
        <div className="p-3.5 text-slate-400 bg-slate-950/40 italic font-mono text-[11.5px] leading-relaxed border-l-2 border-sky-500/70 pl-4 max-h-96 overflow-y-auto custom-scrollbar whitespace-pre-wrap">
          {thought}
        </div>
      )}
    </div>
  );
};

const CodeBlock: React.FC<{ code: string; lang?: string }> = ({ code, lang }) => {
  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 shadow-md my-3 font-mono text-xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 text-[11px] text-slate-400">
        <span className="text-cyan-400 font-semibold uppercase tracking-wider">{lang || "code"}</span>
        <button
          onClick={copyCode}
          className="flex items-center gap-1 hover:text-white transition-colors px-2 py-0.5 rounded hover:bg-slate-800"
        >
          {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-slate-200 custom-scrollbar leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};
