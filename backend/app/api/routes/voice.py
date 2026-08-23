from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel

from app.core.logger import logger
from app.services.audio_service import audio_pipeline

router = APIRouter(prefix="/voice", tags=["voice"])


class SynthesisRequest(BaseModel):
    text: str
    voice: str | None = "en_US-amy-medium"
    speed: float | None = 1.0


@router.get("/status")
async def voice_status():
    """
    Get the health, discovered models, and capabilities of the audio pipelines.
    """
    return audio_pipeline.get_status()


@router.get("/models")
async def list_audio_models():
    """
    List all local Whisper and Piper models found in ai-models/audio/.
    """
    return {
        "whisper_models": audio_pipeline.stt.list_available_models(),
        "tts_voices": audio_pipeline.tts.list_available_voices(),
    }


@router.get("/voices")
async def list_voices():
    """
    List available Text-To-Speech voices.
    """
    return {"voices": audio_pipeline.tts.list_available_voices()}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(None, description="Optional ISO language code (e.g. 'en')"),
):
    """
    Transcribe an uploaded audio file (WAV, MP3, WEBM, M4A) to text using Whisper.
    """
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file provided")

        result = await audio_pipeline.stt.transcribe(
            audio_bytes=contents,
            filename=file.filename or "audio.wav",
            language=language,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
@router.post("/speak")
async def synthesize_speech(request: SynthesisRequest):
    """
    Synthesize text into WAV audio stream.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        audio_bytes = await audio_pipeline.tts.synthesize(
            text=request.text,
            voice=request.voice or "copper_synth",
            speed=request.speed or 1.0,
        )

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=speech.wav",
                "Content-Length": str(len(audio_bytes)),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation")
async def voice_conversation(
    file: UploadFile = File(...),
    session_id: str = Form("voice_session_default"),
):
    """
    End-to-End Voice Conversation Turn:
    Receives user voice, transcribes it, runs agent logic, and returns text + synthesized audio.
    """
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        stt_result = await audio_pipeline.stt.transcribe(audio_bytes)
        user_text = stt_result.get("text", "")

        if not user_text:
            return {
                "transcription": "",
                "response_text": "Could not recognize speech.",
                "audio_base64": None,
            }

        from app.services.chat_service import chat_service

        agent_res = await chat_service.process_message(
            session_id=session_id,
            message=user_text,
        )
        response_text = agent_res.get("response", "")

        tts_audio = await audio_pipeline.tts.synthesize(response_text)
        import base64

        audio_b64 = base64.b64encode(tts_audio).decode("utf-8")

        return {
            "transcription": user_text,
            "response_text": response_text,
            "agent_id": agent_res.get("agent_id", "default"),
            "audio_base64": audio_b64,
            "audio_format": "audio/wav",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream")
async def voice_websocket_stream(websocket: WebSocket):
    """
    Real-time bidirectional WebSocket stream for voice interaction.
    """
    await websocket.accept()
    logger.info("Voice WebSocket connected")
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                raw_audio = message["bytes"]
                stt_res = await audio_pipeline.stt.transcribe(raw_audio)
                await websocket.send_json(
                    {
                        "event": "transcription",
                        "text": stt_res.get("text", ""),
                    }
                )
            elif "text" in message and message["text"]:
                import json

                data = json.loads(message["text"])
                action = data.get("action")
                if action == "synthesize":
                    text = data.get("text", "")
                    audio_out = await audio_pipeline.tts.synthesize(text)
                    await websocket.send_bytes(audio_out)
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket stream error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
