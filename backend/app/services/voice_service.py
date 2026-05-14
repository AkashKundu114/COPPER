from typing import Optional
from app.ai.voice.whisper_engine import transcribe_audio
from app.ai.voice.tts_engine import synthesize_speech, get_available_voices
from app.services.chat_service import chat_service
from app.core.config import settings
from app.core.logger import logger


class VoiceService:
    async def speech_to_text(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        try:
            text = await transcribe_audio(audio_bytes, language)
            logger.info(f"STT result: {text[:80]}...")
            return text
        except Exception as e:
            logger.error(f"STT error: {e}")
            raise

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> bytes:
        try:
            use_openai = bool(settings.OPENAI_API_KEY)
            audio = await synthesize_speech(text, voice, use_openai)
            logger.info(f"TTS generated {len(audio)} bytes")
            return audio
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    async def process_voice_message(
        self,
        audio_bytes: bytes,
        session_id: str,
        language: Optional[str] = None,
    ) -> dict:
        """Full pipeline: STT -> AI -> TTS."""
        transcript = await self.speech_to_text(audio_bytes, language)
        if not transcript:
            return {"transcript": "", "response": "", "audio": b""}

        result = await chat_service.process_message(session_id, transcript)
        response_text = result["response"]

        audio_response = await self.text_to_speech(response_text)

        return {
            "transcript": transcript,
            "response": response_text,
            "agent_type": result.get("agent_type"),
            "audio": audio_response,
        }

    def get_voices(self) -> list[dict]:
        return get_available_voices()


voice_service = VoiceService()
