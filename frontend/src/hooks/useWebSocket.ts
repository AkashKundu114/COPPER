import { useEffect, useCallback } from "react";
import wsService, { WSMessage } from "@/services/websocket";
import { useChatStore } from "@/store/chatStore";

export function useWebSocket(sessionId: string) {
  const { addMessage, appendChunk, finishStream } = useChatStore();

  useEffect(() => {
    wsService.connect(sessionId);

    const unsub = wsService.onMessage((msg: WSMessage) => {
      const { streamingId } = useChatStore.getState();

      if (msg.type === "chunk" && msg.content) {
        // Append to the already-created streaming bubble
        if (streamingId) appendChunk(streamingId, msg.content);
      } else if (msg.type === "done") {
        if (streamingId) finishStream(streamingId);
      } else if (msg.type === "thinking") {
        // "thinking" just means the server acknowledged the message — no new bubble needed
        // The empty assistant bubble was already created by send() below
      } else if (msg.type === "error" && msg.content) {
        if (streamingId) {
          finishStream(streamingId);
        }
        addMessage("assistant", `❌ Error: ${msg.content}`);
      }
    });

    return () => {
      unsub();
    };
  }, [sessionId]);

  const send = useCallback(
    (message: string, provider = "ollama") => {
      // 1. Show user bubble immediately
      addMessage("user", message);
      // 2. Reserve the assistant streaming bubble
      addMessage("assistant", "");
      // 3. Fire to server
      wsService.sendMessage(message, provider);
    },
    [addMessage]
  );

  return { send, isConnected: wsService.isConnected };
}
