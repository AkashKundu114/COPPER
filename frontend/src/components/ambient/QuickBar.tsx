import React, { useState, useEffect, useRef } from "react";
import { Zap } from "lucide-react";
import { ThinkingOrb } from "thinking-orbs";
import { api } from "../../lib/api";
import { MarkdownContent } from "../chat/MarkdownContent";

function getIpcRenderer() {
  if (typeof window !== "undefined" && typeof (window as any).require === "function") {
    try {
      return (window as any).require("electron")?.ipcRenderer;
    } catch {
      return null;
    }
  }
  return null;
}

export function QuickBar() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        getIpcRenderer()?.invoke("quick-bar-hide");
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    // Resize the window based on content
    if (containerRef.current) {
      const height = containerRef.current.offsetHeight;
      getIpcRenderer()?.invoke("quick-bar-resize", height + 16);
    }
  }, [response, loading]);

  const handleSubmit = async (e: React.FormEvent | React.KeyboardEvent) => {
    if (e && "preventDefault" in e) {
      e.preventDefault();
    }
    
    if (!query.trim()) return;
    
    setLoading(true);
    setResponse(null);
    
    try {
      if (query.startsWith("/task ") || query.startsWith("/event ")) {
        const title = query.replace(/^\/(task|event)\s+/, "").trim();
        await api.post("/api/v1/schedule/events", { title, time: "Today", category: "Focus", completed: false });
        setResponse(`**Event scheduled:** ${title}`);
      } else if (query.startsWith("/remind ")) {
        const text = query.slice(8).trim();
        await api.post("/api/v1/reminders/parse", { text });
        setResponse(`**Reminder set for:** ${text}`);
      } else if (query.startsWith("/search ")) {
        const text = query.slice(8).trim();
        const res = await api.post("/api/v1/memory/search", { query: text });
        const items = res.data?.items || res.data || [];
        if (Array.isArray(items) && items.length > 0) {
          setResponse(`Found ${items.length} items.\n\n` + items.map(i => `- ${i.content || i.title || JSON.stringify(i)}`).join("\n"));
        } else {
          setResponse(`No memory items found for: ${text}`);
        }
      } else {
        const res = await api.post("/api/v1/chat/message", { message: query });
        setResponse(res.data?.response || res.data?.message || "Processed your request.");
      }
    } catch (error: any) {
      setResponse(`**Error:** ${error.response?.data?.detail || error.message || "Something went wrong."}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && e.ctrlKey) {
      const ipc = getIpcRenderer();
      ipc?.invoke("quick-bar-focus-main");
      ipc?.invoke("quick-bar-hide");
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div 
      ref={containerRef}
      className="bg-slate-950/95 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col w-[680px] text-white animate-in zoom-in-95 duration-200"
    >
      <div className="flex items-center px-4 py-4 gap-3">
        <Zap className="w-5 h-5 text-accent-400 shrink-0" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask COPPER anything... (Ctrl+Enter for main window)"
          className="bg-transparent text-white text-sm font-sans placeholder-slate-500 w-full outline-none focus:outline-none border-none focus:ring-0 p-0"
          autoFocus
        />
        {loading && (
          <ThinkingOrb state="searching" size={20} theme="dark" />
        )}
      </div>

      {(response || loading) && (
        <div className="px-4 pb-4 pt-1 max-h-[400px] overflow-y-auto custom-scrollbar border-t border-slate-800/50">
          {loading && !response ? (
            <div className="text-sm text-slate-400 flex items-center gap-2 py-2">
              Processing...
            </div>
          ) : (
            <div className="w-full markdown-body font-sans text-[14.5px] leading-relaxed text-slate-300">
              <MarkdownContent content={response || ""} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
