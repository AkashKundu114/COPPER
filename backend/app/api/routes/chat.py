import asyncio
import base64

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

from app.core.telemetry import start_request_trace
from opentelemetry.trace import Status, StatusCode

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
    metrics: dict | None = None
    trace_id: str | None = None


@router.post("/message", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    valid, err = validate_message(req.message)
    if not valid:
        raise HTTPException(status_code=400, detail=err)
    session_id = req.session_id or generate_session_id()
    root_span, trace_id, span_id = start_request_trace(
        "copper.http.request",
        session_id=session_id,
        attributes={
            "copper.session_id": session_id,
            "copper.message": req.message[:200],
            "copper.provider": req.provider.value if hasattr(req.provider, "value") else str(req.provider),
            "copper.endpoint": "/chat/message",
        },
    )
    try:
        result = await chat_service.process_message(
            session_id, req.message, req.provider, db=db, trace_id=trace_id, parent_span=root_span
        )
        for sender, message in [("user", req.message), ("assistant", result["response"])]:
            db.add(ChatHistory(session_id=session_id, sender=sender, message=message))
        db.commit()
        return ChatResponse(
            response=result["response"],
            agent_type=str(result["agent_type"]),
            session_id=session_id,
            guardian_verdict=result.get("guardian_verdict"),
            metrics=result.get("metrics"),
            trace_id=trace_id,
        )
    except Exception as e:
        root_span.record_exception(e)
        root_span.set_status(Status(StatusCode.ERROR, str(e)))
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")
    finally:
        root_span.end()


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
    if records:
        return [r.to_dict() for r in records]

    # Fallback to persistent memory / branch session history
    from app.ai.memory.persistent_memory import persistent_memory

    mem_history = persistent_memory.get_history(session_id)
    if mem_history:
        return [
            {
                "id": idx + 1,
                "session_id": session_id,
                "sender": m.get("role", "user"),
                "message": m.get("content", ""),
                "created_at": None,
            }
            for idx, m in enumerate(mem_history)
        ]

    return []


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, db: Session = Depends(get_db)):
    await chat_service.clear_history(session_id)
    db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
    db.commit()
    return {"message": "History cleared"}


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    active_task: asyncio.Task | None = None

    async def execute_turn(data_payload: dict):
        nonlocal active_task
        message = data_payload.get("message", "")
        mode = data_payload.get("mode", "auto")
        voice = data_payload.get("voice", "en-US-AvaNeural")
        provider = LLMProvider(data_payload.get("provider", "ollama"))
        valid, err = validate_message(message)
        if not valid:
            await manager.send_error(session_id, err)
            return

        root_span, trace_id, span_id = start_request_trace(
            "copper.websocket.request",
            session_id=session_id,
            attributes={
                "copper.session_id": session_id,
                "copper.message": message[:200],
                "copper.mode": mode,
                "copper.provider": provider.value if hasattr(provider, "value") else str(provider),
                "copper.client": "websocket",
            },
        )

        await manager.send_trace_context(session_id, trace_id, span_id)
        await manager.send(session_id, {"type": "thinking", "agent_type": "", "trace_id": trace_id})
        full_response = []
        metrics: dict = {}
        try:
            async for chunk in chat_service.stream_message(
                session_id,
                message,
                provider,
                mode=mode,
                metrics_collector=metrics,
                trace_id=trace_id,
                parent_span=root_span,
            ):
                await manager.send_chunk(session_id, chunk)
                full_response.append(chunk)

            from app.ai.memory.persistent_memory import persistent_memory

            persisted_voice = persistent_memory.get_preference("voice")
            if persisted_voice:
                voice = persisted_voice
            mute_voice = persistent_memory.get_preference("mute_voice", False)

            complete_text = "".join(full_response)
            if complete_text.strip() and not mute_voice:
                try:
                    from app.services.audio_service import audio_pipeline

                    audio_bytes = await audio_pipeline.tts.synthesize(complete_text, voice=voice)
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                    await manager.send(session_id, {"type": "audio_playback", "audio_base64": audio_b64})
                except Exception as e:
                    logger.error(f"TTS synthesis failed for websocket: {e}")

            await manager.send_done(session_id, metrics=metrics, trace_id=trace_id)
        except asyncio.CancelledError:
            logger.info(f"Stream generation cancelled for session {session_id}")
            root_span.set_attribute("copper.cancelled", True)
            raise
        except Exception as e:
            root_span.record_exception(e)
            root_span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.error(f"WebSocket execution error: {e}")
            await manager.send_error(session_id, "Execution error occurred", trace_id=trace_id)
        finally:
            root_span.end()

    try:
        while True:
            data = await websocket.receive_json()

            if "action" in data:
                action = data["action"]
                if action in ("interrupt", "stop_audio"):
                    if active_task and not active_task.done():
                        active_task.cancel()
                        logger.info(f"Interrupted stream for session {session_id}")
                    continue

                from app.core.anomaly_sentinel import sentinel

                if action == "snooze":
                    sentinel.snooze_alert(data.get("alert_id"), int(data.get("duration", 900)))
                elif action == "dismiss":
                    sentinel.dismiss_alert(data.get("alert_id"))
                continue

            # Cancel any previous task still executing
            if active_task and not active_task.done():
                active_task.cancel()

            active_task = asyncio.create_task(execute_turn(data))
    except WebSocketDisconnect:
        if active_task and not active_task.done():
            active_task.cancel()
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if active_task and not active_task.done():
            active_task.cancel()
        manager.disconnect(websocket)


class BranchCreateRequest(BaseModel):
    session_id: str
    message_index: int
    title: str | None = None


class BranchMergeRequest(BaseModel):
    target_session_id: str | None = None


@router.post("/branch")
async def create_branch_endpoint(req: BranchCreateRequest):
    """Creates an independent conversation branch diverging at message_index."""
    try:
        from app.ai.branching.branch_manager import branch_manager

        branch = branch_manager.branch_conversation(
            session_id=req.session_id,
            message_index=req.message_index,
            title=req.title,
        )
        return {"status": "success", "branch": branch}
    except Exception as e:
        logger.error(f"Error creating branch: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/branches/compare")
async def compare_branches_endpoint(a: str, b: str):
    """Compares two conversation branches using natural language semantic diff analysis."""
    try:
        from app.ai.branching.diff_analyzer import diff_analyzer

        diff = await diff_analyzer.compare_branches(branch_a_id=a, branch_b_id=b)
        return {"status": "success", "comparison": diff}
    except Exception as e:
        logger.error(f"Error comparing branches: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/branches/{session_id}")
async def list_branches_endpoint(session_id: str):
    """Lists all branches in the conversation tree for a session."""
    try:
        from app.ai.branching.branch_manager import branch_manager

        branches = branch_manager.list_branches(session_id)
        return {"status": "success", "session_id": session_id, "branches": branches}
    except Exception as e:
        logger.error(f"Error listing branches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/branches/{branch_id}/merge")
async def merge_branch_endpoint(branch_id: str, req: BranchMergeRequest | None = None):
    """Merges branch discoveries and insights back into parent timeline."""
    try:
        from app.ai.branching.branch_manager import branch_manager

        target_id = req.target_session_id if req else None
        res = branch_manager.merge_branch(branch_id, target_session_id=target_id)
        return res
    except Exception as e:
        logger.error(f"Error merging branch {branch_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
