from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
from app.services.voice_service import voice_service
from app.utils.helpers import generate_session_id
from app.core.logger import logger

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    try:
        audio_bytes = await audio.read()
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        text = await voice_service.speech_to_text(audio_bytes, language)
        return {"transcript": text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")


@router.post("/synthesize")
async def synthesize(
    text: str = Form(...),
    voice: Optional[str] = Form(None),
):
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        if len(text) > 4096:
            raise HTTPException(status_code=400, detail="Text too long (max 4096 chars)")

        audio_bytes = await voice_service.text_to_speech(text, voice)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesize error: {e}")
        raise HTTPException(status_code=500, detail="TTS failed")


@router.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
):
    """Full voice pipeline: audio -> STT -> AI -> TTS."""
    try:
        audio_bytes = await audio.read()
        session_id = session_id or generate_session_id()
        result = await voice_service.process_voice_message(audio_bytes, session_id, language)

        return {
            "transcript": result["transcript"],
            "response": result["response"],
            "agent_type": str(result.get("agent_type", "chat")),
            "session_id": session_id,
            "has_audio": len(result["audio"]) > 0,
        }
    except Exception as e:
        logger.error(f"Voice process error: {e}")
        raise HTTPException(status_code=500, detail="Voice processing failed")


@router.get("/voices")
async def get_voices():
    return voice_service.get_voices()


@router.post("/wake-word/trigger")
async def trigger_wake_word():
    from app.ai.voice.wakeword_engine import wake_engine
    wake_engine.simulate_detection()
    return {"triggered": True}
