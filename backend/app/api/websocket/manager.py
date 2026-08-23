from fastapi import WebSocket

from app.core.logger import logger

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self.sessions: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, session_id: str | None = None):
        await ws.accept()
        self.active.append(ws)
        if session_id:
            self.sessions[session_id] = ws
        logger.info(f"WS connected ({len(self.active)} total)")

    def disconnect(self, session_id_or_ws: str | WebSocket = None):
        if isinstance(session_id_or_ws, str):
            ws = self.sessions.pop(session_id_or_ws, None)
            if ws and ws in self.active:
                self.active.remove(ws)
        elif isinstance(session_id_or_ws, WebSocket):
            if session_id_or_ws in self.active:
                self.active.remove(session_id_or_ws)
            self.sessions = {k: v for k, v in self.sessions.items() if v != session_id_or_ws}
        logger.info(f"WS disconnected ({len(self.active)} total)")

    async def send(self, session_id: str, event: dict):
        ws = self.sessions.get(session_id)
        if ws:
            try:
                await ws.send_json(event)
            except Exception:
                self.disconnect(session_id)

    async def send_chunk(self, session_id: str, chunk: str):
        await self.send(session_id, {"type": "agent_speaking", "agent": "COPPER", "text": chunk})

    async def send_done(self, session_id: str):
        await self.send(session_id, {"type": "done"})

    async def send_error(self, session_id: str, error: str):
        await self.send(session_id, {"type": "error", "message": error})

    async def broadcast(self, event: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_alert(self, alert):
        event = {"type": "proactive_intervention", **alert.to_dict()}
        await self.broadcast(event)

    async def push_proactive(self, event: dict):
        event["type"] = "proactive_intervention"
        await self.broadcast(event)

manager = ConnectionManager()
