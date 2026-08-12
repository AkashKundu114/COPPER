from fastapi import WebSocket
from app.core.logger import logger

class ConnectionManager:

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info(f'WS connected ({len(self.active)} total)')

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        logger.info(f'WS disconnected ({len(self.active)} total)')

    async def broadcast(self, event: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
manager = ConnectionManager()