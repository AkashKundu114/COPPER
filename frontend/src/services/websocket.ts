type MessageHandler = (data: WSMessage) => void;

export interface WSMessage {
  type: "chunk" | "done" | "error" | "thinking" | "notification" | "reminder";
  content?: string;
  agent_type?: string;
  title?: string;
  body?: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: MessageHandler[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private sessionId = "";
  private shouldReconnect = true;

  connect(sessionId: string) {
    this.sessionId = sessionId;
    this.shouldReconnect = true;
    const wsBase = import.meta.env.VITE_WS_URL || "ws://localhost:8000/api/v1";
    const url = `${wsBase}/chat/ws/${sessionId}`;

    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => console.log("[WS] Connected:", sessionId);

    this.ws.onmessage = (e) => {
      try {
        const data: WSMessage = JSON.parse(e.data);
        this.handlers.forEach((h) => h(data));
      } catch (err) {
        console.error("[WS] Parse error:", err);
      }
    };

    this.ws.onclose = () => {
      console.log("[WS] Disconnected");
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(this.sessionId), 3000);
      }
    };

    this.ws.onerror = (e) => console.error("[WS] Error:", e);
  }

  send(data: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  sendMessage(message: string, provider = "ollama") {
    return this.send({ message, provider });
  }

  onMessage(handler: MessageHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
export default wsService;
