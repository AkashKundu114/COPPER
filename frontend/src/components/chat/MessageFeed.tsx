import { useEffect, useRef } from "react";
import { type BrainLine } from "../../lib/useBrainSocket";
import { type AgentStats } from "../../lib/api";
import { Bot, User } from "lucide-react";

interface MessageFeedProps {
  lines: BrainLine[];
  agentStats: Record<string, AgentStats>;
  thinking: boolean;
  activeAgent: string | null;
}

export function MessageFeed({ lines, agentStats, thinking, activeAgent }: MessageFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [lines, thinking]);

  return (
    <div ref={feedRef} className="flex-1 w-full max-w-4xl mx-auto overflow-y-auto px-6 py-8 space-y-8 custom-scrollbar">
      {lines.map((line, i) => {
        const isUser = line.source === "user";
        const agentName = line.agent_id ? (agentStats[line.agent_id]?.name || line.agent_id) : "C.O.P.P.E.R.";
        
        return (
          <div key={i} className={`flex gap-4 ${isUser ? "flex-row-reverse" : "flex-row"} animate-slide-up`}>
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? "bg-bg-raised text-text" : "bg-bg-panel border border-border text-accent"}`}>
              {isUser ? <User size={16} /> : <Bot size={16} />}
            </div>
            
            <div className={`flex flex-col max-w-[80%] ${isUser ? "items-end" : "items-start"}`}>
              <span className="text-xs text-text-muted mb-1 font-medium px-1">
                {isUser ? "You" : agentName}
              </span>
              <div className={`px-4 py-3 rounded-2xl ${isUser ? "bg-bg-raised text-text" : "bg-bg-panel border border-border text-text"}`}>
                <p className="whitespace-pre-wrap leading-relaxed text-sm">
                  {line.content}
                </p>
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
