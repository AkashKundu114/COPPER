import { useEffect, useRef, useState, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Trash2, Mic, MicOff } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useVoice } from "@/hooks/useVoice";
import { MessageBubble } from "./MessageBubble";
import { GuardianChallengeModal, GuardianVerdict } from "./GuardianChallengeModal";
import { chatAPI } from "@/services/api";

export function ChatWindow() {
  const [input, setInput] = useState("");
  const [pendingVerdict, setPendingVerdict] = useState<GuardianVerdict | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { messages, sessionId, isLoading, clearMessages, provider, addMessage } = useChatStore();
  const { send } = useWebSocket(sessionId);
  const { isRecording, isProcessing, startRecording, stopRecording, transcribe } = useVoice();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Non-streaming path (used when a guardian verdict may need to be inspected
  // before rendering, e.g. from a REST caller). WebSocket streaming path
  // still exists for normal chat; the challenge check here catches direct
  // POST /chat/message callers such as the future mobile client.
  const checkGuardianResponse = async (msg: string) => {
    const { data } = await chatAPI.sendMessage(msg, sessionId, provider);
    if (data.guardian_verdict && data.guardian_verdict.level >= 2) {
      setPendingVerdict(data.guardian_verdict);
      addMessage("assistant", data.response, data.agent_type);
      return true;
    }
    return false;
  };

  const handleSend = async () => {
    const msg = input.trim();
    if (!msg || isLoading) return;
    setInput("");
    send(msg, provider);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoice = async () => {
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        const text = await transcribe(blob);
        if (text) setInput(text);
      }
    } else {
      await startRecording();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-copper-500 animate-pulse" />
          <span className="text-sm font-medium text-gray-300">COPPER Chat</span>
          <span className="text-xs text-gray-600 font-mono">{sessionId.slice(0, 8)}</span>
        </div>
        <button
          onClick={clearMessages}
          className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          title="Clear chat"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full gap-4 text-center"
            >
              <div className="text-6xl">🤖</div>
              <h2 className="text-xl font-semibold glow-text">COPPER Online</h2>
              <p className="text-gray-500 text-sm max-w-xs">
                Your AI productivity assistant. Ask me anything — code, automation, research, reminders.
              </p>
            </motion.div>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-white/5">
        <div className="flex items-end gap-2 glass rounded-xl p-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message COPPER... (Shift+Enter for newline)"
            rows={1}
            className="flex-1 bg-transparent resize-none text-sm text-gray-200 placeholder-gray-600 outline-none max-h-32 py-1 px-2"
            style={{ lineHeight: "1.5" }}
          />
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              onClick={handleVoice}
              disabled={isProcessing}
              className={`p-2 rounded-lg transition-all ${
                isRecording
                  ? "text-red-400 bg-red-400/10 animate-pulse"
                  : "text-gray-500 hover:text-copper-400 hover:bg-copper-400/10"
              }`}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-2 rounded-lg bg-copper-600 hover:bg-copper-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      <GuardianChallengeModal
        verdict={pendingVerdict}
        sessionId={sessionId}
        onResolved={() => setPendingVerdict(null)}
        onClose={() => setPendingVerdict(null)}
      />
    </div>
  );
}
