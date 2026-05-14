import json
from typing import Optional
from fastapi import WebSocket
from app.core.logger import logger


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}  # session_id -> WebSocket

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id} ({len(self.active)} total)")

    def disconnect(self, session_id: str):
        self.active.pop(session_id, None)
        logger.info(f"WebSocket disconnected: {session_id}")

    async def send(self, session_id: str, data: dict) -> bool:
        ws = self.active.get(session_id)
        if not ws:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception as e:
            logger.error(f"WebSocket send error ({session_id}): {e}")
            self.disconnect(session_id)
            return False

    async def send_text(self, session_id: str, text: str) -> bool:
        return await self.send(session_id, {"type": "text", "content": text})

    async def send_chunk(self, session_id: str, chunk: str) -> bool:
        return await self.send(session_id, {"type": "chunk", "content": chunk})

    async def send_done(self, session_id: str, agent_type: str = "chat") -> bool:
        return await self.send(session_id, {"type": "done", "agent_type": agent_type})

    async def send_error(self, session_id: str, error: str) -> bool:
        return await self.send(session_id, {"type": "error", "content": error})

    async def send_notification(self, session_id: str, title: str, body: str) -> bool:
        return await self.send(session_id, {
            "type": "notification",
            "title": title,
            "body": body,
        })

    async def broadcast(self, data: dict):
        disconnected = []
        for sid, ws in self.active.items():
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(sid)
        for sid in disconnected:
            self.disconnect(sid)

    def get_active_sessions(self) -> list[str]:
        return list(self.active.keys())

    def is_connected(self, session_id: str) -> bool:
        return session_id in self.active


manager = ConnectionManager()
