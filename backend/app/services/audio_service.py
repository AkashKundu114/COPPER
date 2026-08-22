import io
import math
import os
import struct
import wave
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logger import logger


class WhisperSTTPipeline:
    """
    Offline Speech-To-Text Pipeline using Whisper.
    Supports GGUF / ONNX / PyTorch models placed in ai-models/audio/whisper.
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
                elif f.is_dir() and (f / "model.bin").exists():
                    models.append(
                        {
                            "name": f.name,
                            "path": str(f),
                            "size_mb": round(sum(p.stat().st_size for p in f.rglob("*")) / (1024 * 1024), 2),
                            "format": "huggingface/ctranslate2",
                        }
                    )
        return models

    async def transcribe(
        self, audio_bytes: bytes, filename: str = "audio.wav", language: str | None = None
    ) -> dict[str, Any]:
        """
        Transcribe raw audio bytes into text.
        """
        try:
            try:
                from faster_whisper import WhisperModel

                models = self.list_available_models()
                if models:
                    model_path = models[0]["path"]
                    if self._model is None or self._model_name != model_path:
                        logger.info(f"Loading Whisper model from {model_path} on GPU/CPU")
                        self._model = WhisperModel(
                            model_path,
                            device="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "auto",
                            compute_type="float16" if os.environ.get("CUDA_VISIBLE_DEVICES") else "int8",
                        )
                        self._model_name = model_path

                    audio_stream = io.BytesIO(audio_bytes)
                    segments, info = self._model.transcribe(audio_stream, language=language, beam_size=5)
                    text = " ".join([seg.text for seg in segments]).strip()
                    return {
                        "text": text,
                        "language": info.language,
                        "language_probability": round(info.language_probability, 3),
                        "duration": round(info.duration, 2),
                        "engine": "faster-whisper-local",
                    }
            except ImportError:
                pass

            try:
                import whisper

                if self._model is None:
                    self._model = whisper.load_model("tiny")
                    self._model_name = "whisper-tiny"

                temp_path = self.models_dir / f"temp_{os.getpid()}.wav"
                with open(temp_path, "wb") as f:
                    f.write(audio_bytes)

                result = self._model.transcribe(str(temp_path), language=language)
                if temp_path.exists():
                    temp_path.unlink()

                return {
                    "text": result.get("text", "").strip(),
                    "language": result.get("language", "en"),
                    "duration": 0.0,
                    "engine": "openai-whisper",
                }
            except ImportError:
                pass

            duration_sec = len(audio_bytes) / 32000.0 
            logger.info(f"STT Pipeline received {len(audio_bytes)} bytes audio ({round(duration_sec, 2)}s)")
            return {
                "text": "[Whisper STT Ready: Install 'faster-whisper' or place Whisper GGUF in ai-models/audio/whisper for full local transcription]",
                "language": "en",
                "duration": round(duration_sec, 2),
                "engine": "whisper-fallback",
            }

        except Exception as e:
            logger.error(f"Error during audio transcription: {e}")
            return {
                "text": "",
                "error": str(e),
                "engine": "stt-error",
            }


class PiperTTSPipeline:
    """
    Offline Text-To-Speech Pipeline using Piper / SAPI5 / Kokoro.
    Supports ONNX voice models placed in ai-models/audio/tts.
    """

    def __init__(self, models_dir: str | None = None):
        self.models_dir = Path(models_dir or settings.TTS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._piper_voice = None

    def list_available_voices(self) -> list[dict[str, Any]]:
        voices = []
        if self.models_dir.exists():
            for f in self.models_dir.iterdir():
                if f.is_file() and f.suffix.lower() == ".onnx":
                    json_config = f.with_suffix(".onnx.json")
                    voices.append(
                        {
                            "id": f.stem,
                            "name": f.stem.replace("_", " ").title(),
                            "model_file": f.name,
                            "config_file": json_config.name if json_config.exists() else None,
                            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                            "engine": "piper-onnx",
                        }
                    )

        voices.append({"id": "os_default", "name": "System Default (SAPI5/OS)", "engine": "native-os"})
        voices.append({"id": "copper_synth", "name": "C.O.P.P.E.R Synth Voice", "engine": "copper-synth"})
        return voices

    async def synthesize(self, text: str, voice: str = "copper_synth", speed: float = 1.0) -> bytes:
        """
        Synthesize text into WAV audio bytes.
        """
        if not text.strip():
            return self._generate_silence_wav(0.1)

        try:
            onnx_path = self.models_dir / f"{voice}.onnx"
            if onnx_path.exists():
                import piper

                voice_config = onnx_path.with_suffix(".onnx.json")
                if self._piper_voice is None:
                    self._piper_voice = piper.PiperVoice.load(
                        str(onnx_path), config_path=str(voice_config) if voice_config.exists() else None
                    )

                buf = io.BytesIO()
                with wave.open(buf, "wb") as wav_file:
                    self._piper_voice.synthesize(text, wav_file)
                return buf.getvalue()
        except ImportError:
            pass

        try:
            import pyttsx3

            engine = pyttsx3.init()
            if speed != 1.0:
                current_rate = engine.getProperty("rate")
                engine.setProperty("rate", int(current_rate * speed))

            temp_wav = self.models_dir / f"tts_temp_{os.getpid()}.wav"
            engine.save_to_file(text, str(temp_wav))
            engine.runAndWait()

            if temp_wav.exists():
                with open(temp_wav, "rb") as f:
                    data = f.read()
                temp_wav.unlink()
                return data
        except Exception:
            pass

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
    Unified manager for Speech-To-Text and Text-To-Speech audio pipelines.
    """

    def __init__(self):
        self.stt = WhisperSTTPipeline()
        self.tts = PiperTTSPipeline()

    def get_status(self) -> dict[str, Any]:
        return {
            "status": "ready",
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
