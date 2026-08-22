from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.websocket.socket_manager import manager
from app.core.constants import LLMProvider
from app.core.logger import logger
from app.database.models.history import ChatHistory
from app.database.postgres import get_db
from app.services.chat_service import chat_service
from app.utils.helpers import generate_session_id
from app.utils.validators import validate_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    provider: LLMProvider = LLMProvider.OLLAMA
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    agent_type: str
    session_id: str
    guardian_verdict: dict | None = None


@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    valid, err = validate_message(req.message)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    session_id = req.session_id or generate_session_id()
    try:
        result = await chat_service.process_message(session_id, req.message, req.provider, db=db)
        for sender, message in [("user", req.message), ("assistant", result["response"])]:
            db.add(ChatHistory(session_id=session_id, sender=sender, message=message))
        db.commit()
        return ChatResponse(
            response=result["response"],
            agent_type=str(result["agent_type"]),
            session_id=session_id,
            guardian_verdict=result.get("guardian_verdict"),
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")


@router.get("/stream")
async def stream_message(message: str, session_id: str | None = None, provider: LLMProvider = LLMProvider.OLLAMA):
    valid, err = validate_message(message)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    session_id = session_id or generate_session_id()

    async def event_stream():
        async for chunk in chat_service.stream_message(session_id, message, provider):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history/{session_id}")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at)
        .limit(100)
        .all()
    )
    return [r.to_dict() for r in records]


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, db: Session = Depends(get_db)):
    await chat_service.clear_history(session_id)
    db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
    db.commit()
    return {"message": "History cleared"}


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()

            if "action" in data:
                action = data["action"]
                from app.core.anomaly_sentinel import sentinel

                if action == "snooze":
                    sentinel.snooze_alert(data.get("alert_id"), int(data.get("duration", 900)))
                elif action == "dismiss":
                    sentinel.dismiss_alert(data.get("alert_id"))
                continue

            message = data.get("message", "")
            provider = LLMProvider(data.get("provider", "ollama"))
            valid, err = validate_message(message)
            if not valid:
                await manager.send_error(session_id, err)
                continue
            await manager.send(session_id, {"type": "thinking", "agent_type": ""})
            full_response = []
            async for chunk in chat_service.stream_message(session_id, message, provider):
                await manager.send_chunk(session_id, chunk)
                full_response.append(chunk)
            await manager.send_done(session_id)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_error(session_id, str(e))
        manager.disconnect(session_id)
