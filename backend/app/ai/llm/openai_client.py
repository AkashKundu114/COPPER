from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logger import logger
from app.core.data_firewall import classify_and_redact

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _firewall_messages(messages: list[dict]) -> tuple[list[dict], int, str]:
    """Redacts every message's content, returns (clean_messages, redaction_count, worst_class)."""
    cleaned = []
    total_redactions = 0
    worst = "public"
    severity = ["public", "personal", "sensitive", "secret"]
    for m in messages:
        r = classify_and_redact(m.get("content", "") or "")
        cleaned.append({**m, "content": r.redacted_text})
        total_redactions += r.redaction_count
        if severity.index(r.classification.value) > severity.index(worst):
            worst = r.classification.value
    return cleaned, total_redactions, worst


def _log_external_access(db: Optional[Session], session_id: Optional[str], summary: str) -> None:
    if db is None:
        return
    from app.services.guardian_service import guardian_service
    guardian_service.log(
        db=db,
        category="external_api_accessed",
        actor="openai_client",
        summary=summary,
        session_id=session_id,
        scope="cloud",
    )


async def openai_chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
) -> str:
    client = get_openai_client()
    model = model or settings.OPENAI_MODEL
    clean_messages, redactions, worst_class = _firewall_messages(messages)
    if redactions:
        logger.info(f"Data firewall redacted {redactions} item(s) (class={worst_class}) before OpenAI call")
    _log_external_access(db, session_id, f"Chat completion via OpenAI ({model}); {redactions} redaction(s)")
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=clean_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        raise


async def openai_stream_chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    client = get_openai_client()
    model = model or settings.OPENAI_MODEL
    clean_messages, redactions, worst_class = _firewall_messages(messages)
    if redactions:
        logger.info(f"Data firewall redacted {redactions} item(s) (class={worst_class}) before OpenAI stream")
    _log_external_access(db, session_id, f"Streaming chat via OpenAI ({model}); {redactions} redaction(s)")
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=clean_messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"OpenAI stream error: {e}")
        raise


async def openai_transcribe(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
) -> str:
    client = get_openai_client()
    _log_external_access(db, session_id, "Audio transcription via OpenAI Whisper API")
    try:
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        transcript = await client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        return transcript.text
    except Exception as e:
        logger.error(f"OpenAI transcribe error: {e}")
        raise


async def openai_tts(
    text: str,
    voice: str = None,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
) -> bytes:
    client = get_openai_client()
    voice = voice or settings.TTS_VOICE
    r = classify_and_redact(text)
    if r.redaction_count:
        logger.info(f"Data firewall redacted {r.redaction_count} item(s) before OpenAI TTS")
    _log_external_access(db, session_id, "Text-to-speech via OpenAI TTS API")
    try:
        response = await client.audio.speech.create(
            model=settings.TTS_MODEL,
            voice=voice,
            input=r.redacted_text,
        )
        return response.content
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        raise
