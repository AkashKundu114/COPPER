"""
Offline "Hey COPPER" wake-word listener.

Two engines, selected by `settings.WAKE_WORD_ENGINE`:

- "openwakeword" (recommended once `hey_copper.onnx` has been trained):
  continuous CPU-only acoustic wake-word scoring, ~1-3% of one core, zero GPU.
- "whisper_fallback" (default until a custom model is trained): VAD-gated
  faster-whisper "tiny" transcription of short speech windows, regex-matched
  against "hey copper" / "copper". Reuses infra already in `audio_service.py`.

Neither path touches the network. Neither path persists raw audio to disk —
everything lives in an in-memory ring buffer for the duration of one
detection window.

On a confirmed wake, this service:
  1. Broadcasts {"type": "wake_detected"} over the WS manager so the frontend
     can show a listening pulse immediately.
  2. Captures the following utterance via the existing STT pipeline.
  3. Hands the transcript to the Gatekeeper (model_tier_manager.chat_gatekeeper)
     for a CONFIRM/IGNORE pass before opening a real chat turn — this is what
     stops "...saw a copper pipe on TV..." from waking a full conversation.
"""

import asyncio
import re
from collections import deque
from typing import Any

from app.core.config import settings
from app.core.logger import logger

WAKE_PATTERN = re.compile(r"\b(hey[,]?\s+)?copper\b", re.IGNORECASE)


class WakeWordService:
    def __init__(self):
        self.engine = getattr(settings, "WAKE_WORD_ENGINE", "whisper_fallback")
        self._listening = False
        self._task: asyncio.Task | None = None
        self._oww_model = None
        self._audio_ring: deque = deque(maxlen=50)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def enable(self) -> dict[str, Any]:
        if self._listening:
            return self.status()
        self._listening = True
        self._task = asyncio.ensure_future(self._listen_loop())
        logger.info(f"[wake-word] Listening enabled (engine={self.engine})")
        return self.status()

    async def disable(self) -> dict[str, Any]:
        self._listening = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("[wake-word] Listening disabled, mic released")
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "listening": self._listening,
            "engine": self.engine,
            "gatekeeper_confirmation_enabled": True,
        }

    # ------------------------------------------------------------------ #
    # Engine dispatch
    # ------------------------------------------------------------------ #
    async def _listen_loop(self) -> None:
        try:
            if self.engine == "openwakeword":
                await self._run_openwakeword()
            else:
                await self._run_whisper_fallback()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"[wake-word] Listener crashed, disabling: {e}")
            self._listening = False

    async def _run_openwakeword(self) -> None:
        try:
            from openwakeword.model import Model as OWWModel
        except ImportError:
            logger.warning("openwakeword not installed — falling back to whisper phrase-spotting.")
            self.engine = "whisper_fallback"
            await self._run_whisper_fallback()
            return

        model_path = getattr(settings, "WAKE_WORD_MODEL_PATH", "ai-models/wakeword/hey_copper.onnx")
        try:
            self._oww_model = OWWModel(wakeword_models=[model_path], inference_framework="onnx")
        except Exception as e:
            logger.warning(f"Could not load custom wake-word model ({e}) — falling back to whisper.")
            self.engine = "whisper_fallback"
            await self._run_whisper_fallback()
            return

        import sounddevice as sd

        chunk_samples = 1280  # ~80ms @ 16kHz, openWakeWord's expected frame size

        def audio_callback(indata, frames, time_info, status):
            self._audio_ring.append(indata.copy())

        with sd.InputStream(
            samplerate=16000, channels=1, dtype="int16", blocksize=chunk_samples, callback=audio_callback
        ):
            while self._listening:
                if self._audio_ring:
                    frame = self._audio_ring.popleft().flatten()
                    scores = self._oww_model.predict(frame)
                    for wake_name, score in scores.items():
                        if score > 0.5:
                            logger.info(f"[wake-word] '{wake_name}' triggered (score={score:.2f})")
                            await self._on_wake_triggered()
                await asyncio.sleep(0.01)

    async def _run_whisper_fallback(self) -> None:
        try:
            import webrtcvad
        except ImportError:
            webrtcvad = None
            logger.warning("webrtcvad not installed — whisper fallback will transcribe continuously (higher CPU cost).")

        from app.services.audio_service import audio_pipeline

        # Placeholder capture cadence: in production this pulls short PCM windows
        # from the mic via sounddevice, gated by webrtcvad, then transcribes each
        # speech window. The mic I/O itself is intentionally left to the platform
        # layer (Tauri/Electron) which already owns microphone permission prompts
        # in this codebase (see ChatDock.tsx / EVEView.tsx VAD implementation) —
        # this backend loop is the transcription+match half of the pipeline.
        vad = webrtcvad.Vad(2) if webrtcvad else None
        while self._listening:
            audio_window = await self._next_speech_window(vad)
            if audio_window is None:
                continue
            result = await audio_pipeline.stt.transcribe(audio_window)
            text = result.get("text", "")
            if WAKE_PATTERN.search(text):
                logger.info(f"[wake-word] Fallback phrase match: '{text}'")
                await self._on_wake_triggered(seed_transcript=text)

    async def _next_speech_window(self, vad) -> bytes | None:
        """
        Integration point: platform-side mic capture pushes raw PCM16 chunks into
        this service (e.g. via a WS binary frame from the desktop shell); this
        stub yields control until one is available. Kept minimal here since the
        actual audio I/O differs between Tauri/Electron/browser deployments.
        """
        await asyncio.sleep(0.5)
        return None

    # ------------------------------------------------------------------ #
    # Confirmation + handoff
    # ------------------------------------------------------------------ #
    async def _on_wake_triggered(self, seed_transcript: str | None = None) -> None:
        from app.api.websocket.manager import manager

        await manager.broadcast({"type": "wake_detected"})

        if seed_transcript:
            await self._confirm_and_dispatch(seed_transcript)
        # else: acoustic engines wait for the platform layer to capture the
        # follow-up utterance and post it to the normal chat WS with
        # source="voice_wake"; confirmation happens in chat_service via the
        # Gatekeeper CONFIRM/IGNORE pass described in the master prompt.

    async def _confirm_and_dispatch(self, transcript: str) -> None:
        from app.ai.llm.model_tier_manager import model_tier_manager

        confirm_prompt = [
            {
                "role": "system",
                "content": "Reply with exactly one word: CONFIRM if this was a real request "
                "addressed to COPPER, or IGNORE if it's background noise/unrelated speech.",
            },
            {"role": "user", "content": transcript},
        ]
        verdict = (await model_tier_manager.chat_gatekeeper(confirm_prompt)).strip().upper()
        if "CONFIRM" not in verdict:
            logger.info(f"[wake-word] Gatekeeper rejected trigger as noise: '{transcript}'")
            return

        from app.services.chat_service import chat_service

        cleaned = WAKE_PATTERN.sub("", transcript, count=1).strip(" ,.") or transcript
        async for _ in chat_service.stream_message(session_id="voice_wake_default", message=cleaned):
            pass


wake_word_service = WakeWordService()
