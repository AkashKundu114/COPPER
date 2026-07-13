from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.services.orchestrator import handle_message
from app.api.websocket.manager import manager
from app.core.logger import logger

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    message: str


@router.post("/message")
async def send_message(req: MessageRequest):
    return await handle_message(req.message)


@router.websocket("/ws")
async def chat_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            message = data.get("message", "")
            if message.strip():
                await handle_message(message)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        logger.error(f"WS error: {e}")
        manager.disconnect(ws)
