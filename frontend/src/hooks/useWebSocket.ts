import { useEffect, useCallback } from "react";
import wsService, { WSMessage } from "@/services/websocket";
import { useChatStore } from "@/store/chatStore";

export function useWebSocket(sessionId: string) {
  const { addMessage, appendChunk, finishStream } = useChatStore();

  useEffect(() => {
    wsService.connect(sessionId);

    const unsub = wsService.onMessage((msg: WSMessage) => {
      if (msg.type === "chunk" && msg.content) {
        const { streamingId } = useChatStore.getState();
        if (streamingId) appendChunk(streamingId, msg.content);
      } else if (msg.type === "done") {
        const { streamingId } = useChatStore.getState();
        if (streamingId) finishStream(streamingId);
      } else if (msg.type === "thinking") {
        addMessage("assistant", "");
      } else if (msg.type === "error" && msg.content) {
        const { streamingId } = useChatStore.getState();
        if (streamingId) finishStream(streamingId);
        addMessage("assistant", `❌ Error: ${msg.content}`);
      }
    });

    return () => {
      unsub();
    };
  }, [sessionId]);

  const send = useCallback(
    (message: string, provider = "ollama") => {
      addMessage("user", message);
      addMessage("assistant", "");
      wsService.sendMessage(message, provider);
    },
    [addMessage]
  );

  return { send, isConnected: wsService.isConnected };
}
