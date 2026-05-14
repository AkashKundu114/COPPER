import { motion } from "framer-motion";
import { Message } from "@/store/chatStore";
import { AGENT_ICONS, AGENT_LABELS, formatRelativeTime } from "@/utils/constants";
import { TypingAnimation } from "./TypingAnimation";

interface Props { message: Message; }

function renderContent(content: string) {
  // Basic markdown: code blocks, inline code, bold
  const parts = content.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const lines = part.slice(3, -3).split("\n");
      const lang = lines[0].trim();
      const code = lines.slice(1).join("\n");
      return (
        <pre key={i} className="bg-dark-800 rounded-lg p-3 my-2 overflow-x-auto text-sm font-mono">
          {lang && <div className="text-copper-400 text-xs mb-2">{lang}</div>}
          <code className="text-green-300">{code}</code>
        </pre>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i} className="bg-dark-600 text-copper-300 rounded px-1.5 py-0.5 text-sm font-mono">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm
        ${isUser ? "bg-copper-600" : "bg-dark-600 border border-copper-600/30"}`}>
        {isUser ? "U" : "C"}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        {!isUser && message.agentType && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <span>{AGENT_ICONS[message.agentType]}</span>
            <span>{AGENT_LABELS[message.agentType] || message.agentType}</span>
          </div>
        )}

        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? "bg-copper-600/20 border border-copper-600/30 text-gray-100 rounded-tr-sm"
            : "bg-dark-700 border border-white/5 text-gray-200 rounded-tl-sm"
          }`}>
          {message.isStreaming && !message.content
            ? <TypingAnimation />
            : <div className="prose-copper">{renderContent(message.content)}</div>
          }
          {message.isStreaming && message.content && (
            <span className="inline-block w-0.5 h-4 bg-copper-500 ml-0.5 animate-pulse" />
          )}
        </div>

        <span className="text-xs text-gray-600">
          {formatRelativeTime(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}
