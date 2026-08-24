import io
import math
import os
import re
import struct
import wave
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logger import logger


class WhisperSTTPipeline:
    """
    Offline Speech-To-Text Pipeline using faster-whisper.
    Automatically loads local 'tiny' or configured model.
    """

    def __init__(self, models_dir: str | None = None):
        self.models_dir = Path(models_dir or settings.WHISPER_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self._model_name = None

    def list_available_models(self) -> list[dict[str, Any]]:
        models = []
        if self.models_dir.exists():
            for f in self.models_dir.iterdir():
                if f.is_file() and f.suffix.lower() in [".bin", ".gguf", ".onnx", ".pt"]:
                    models.append(
                        {
                            "name": f.name,
                            "path": str(f),
                            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                            "format": f.suffix[1:].lower(),
                        }
                    )
        return models

    async def transcribe(
        self, audio_bytes: bytes, filename: str = "audio.wav", language: str | None = None
    ) -> dict[str, Any]:
        """
        Transcribe raw audio bytes into text using faster-whisper.
        """
        try:
            from faster_whisper import WhisperModel

            if self._model is None:
                logger.info("Initializing faster-whisper (tiny) STT Engine...")
                self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
                self._model_name = "faster-whisper-tiny"

            audio_stream = io.BytesIO(audio_bytes)
            segments, info = self._model.transcribe(audio_stream, language=language, beam_size=5)
            text = " ".join([seg.text for seg in segments]).strip()

            return {
                "text": text,
                "language": info.language,
                "language_probability": round(info.language_probability, 3),
                "duration": round(info.duration, 2),
                "engine": "faster-whisper",
            }
        except Exception as e:
            logger.warning(f"Error during audio transcription: {e}")
            return {
                "text": "",
                "error": str(e),
                "engine": "stt-error",
            }


class PiperTTSPipeline:
    """
    High-fidelity Neural & Offline Text-To-Speech Pipeline.
    Tiers:
    1. pyttsx3 / Windows SAPI5 (Offline native WAV)
    2. edge-tts (High fidelity Neural AI Voice)
    3. Synthetic tone generator fallback
    """

    def __init__(self, models_dir: str | None = None):
        self.models_dir = Path(models_dir or settings.TTS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._piper_voice = None

    def list_available_voices(self) -> list[dict[str, Any]]:
        return [
            {"id": "os_default", "name": "Operating System Default Voice", "engine": "windows-sapi5"},
            {"id": "copper_synth", "name": "C.O.P.P.E.R. Synthetic Voice", "engine": "internal"},
            {"id": "en-US-AvaNeural", "name": "Ava (Neural Female - Ultra Realistic)", "engine": "edge-tts"},
            {"id": "en-US-JennyNeural", "name": "Jenny (Neural Female)", "engine": "edge-tts"},
            {"id": "en-US-GuyNeural", "name": "Guy (Neural Male)", "engine": "edge-tts"},
            {"id": "zira", "name": "Microsoft Zira (Offline Windows Female)", "engine": "windows-sapi5"},
            {"id": "david", "name": "Microsoft David (Offline Windows Male)", "engine": "windows-sapi5"},
        ]

    async def synthesize(self, text: str, voice: str = "en-US-AvaNeural", speed: float = 1.0) -> bytes:
        """
        Synthesize text into WAV audio bytes.
        """
        clean_text = text.strip()
        if "<think>" in clean_text:
            clean_text = clean_text.split("</think>")[-1].strip()

        clean_text = re.sub(r"```[\s\S]*?```", " Code snippet attached. ", clean_text)
        clean_text = re.sub(r"[*#_`>]", "", clean_text)
        clean_text = clean_text.strip()

        if not clean_text:
            return self._generate_silence_wav(0.1)

        # 1. Try edge-tts if neural voice requested
        if "neural" in voice.lower() or "edge" in voice.lower():
            try:
                import edge_tts

                target_voice = voice if "Neural" in voice else "en-US-AvaNeural"
                communicate = edge_tts.Communicate(clean_text, target_voice)
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                if chunks:
                    return b"".join(chunks)
            except Exception as e:
                logger.info(f"edge-tts unavailable: {e}")

        # 2. Try pyttsx3 for standard WAV synthesis or fallback
        try:
            import pyttsx3

            engine = pyttsx3.init()
            voices = engine.getProperty("voices")

            if voice and voice.lower() in ["zira", "female"]:
                for v in voices:
                    if "zira" in v.name.lower() or "female" in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break

            if speed != 1.0:
                current_rate = engine.getProperty("rate")
                engine.setProperty("rate", int(current_rate * speed))

            temp_wav = self.models_dir / f"tts_temp_{os.getpid()}_{int(math.floor(speed * 100))}.wav"
            engine.save_to_file(clean_text, str(temp_wav))
            engine.runAndWait()

            if temp_wav.exists():
                with open(temp_wav, "rb") as f:
                    data = f.read()
                try:
                    temp_wav.unlink()
                except Exception:
                    pass
                if len(data) > 44 and data[:4] == b"RIFF":
                    return data
        except Exception as e:
            logger.debug(f"pyttsx3 synthesis unavailable: {e}")

        return self._generate_beeps_wav(duration=0.6, freq=440.0)

    def _generate_silence_wav(self, duration: float = 0.5, sample_rate: int = 22050) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            num_samples = int(duration * sample_rate)
            wav.writeframes(b"\x00\x00" * num_samples)
        return buf.getvalue()

    def _generate_beeps_wav(self, duration: float = 0.5, freq: float = 440.0, sample_rate: int = 22050) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            num_samples = int(duration * sample_rate)
            frames = bytearray()
            for i in range(num_samples):
                envelope = max(0.0, 1.0 - (i / num_samples))
                val = int(math.sin(2.0 * math.pi * freq * (i / sample_rate)) * 16384 * envelope)
                frames.extend(struct.pack("<h", val))
            wav.writeframes(frames)
        return buf.getvalue()


class AudioPipelineManager:
    """
    Orchestrates STT and TTS pipelines with local caching and hardware acceleration.
    """

    def __init__(self):
        self.stt = WhisperSTTPipeline()
        self.tts = PiperTTSPipeline()

    def get_status(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "stt_engine": "faster-whisper",
            "stt_models_available": len(self.stt.list_available_models()) + 1,
            "tts_engine": "edge-tts + Windows SAPI5 (Microsoft Zira)",
            "tts_voices_available": len(self.tts.list_available_voices()),
            "stt_models": self.stt.list_available_models(),
            "tts_voices": self.tts.list_available_voices(),
            "models_dir": str(settings.AUDIO_MODELS_DIR),
        }

    async def process_voice_turn(
        self, audio_bytes: bytes, session_id: str = "voice_session"
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        End-to-End Voice Loop:
        Audio Input -> STT -> Agent Stream -> TTS Response
        """
        stt_result = await self.stt.transcribe(audio_bytes)
        user_text = stt_result.get("text", "")

        yield {
            "type": "transcription",
            "text": user_text,
            "duration": stt_result.get("duration", 0),
            "engine": stt_result.get("engine", "whisper"),
        }

        if not user_text:
            return

        from app.services.chat_service import chat_service

        agent_response_full = []

        async for chunk in chat_service.stream_message(session_id=session_id, message=user_text):
            agent_response_full.append(chunk)
            yield {
                "type": "text_chunk",
                "chunk": chunk,
            }

        full_response_text = "".join(agent_response_full)

        tts_audio = await self.tts.synthesize(full_response_text)
        yield {
            "type": "audio_response",
            "audio_size_bytes": len(tts_audio),
            "text": full_response_text,
        }


audio_pipeline = AudioPipelineManager()
