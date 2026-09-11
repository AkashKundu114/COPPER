import asyncio
import json
import os
import uuid
import wave
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    SOUNDDEVICE_AVAILABLE = False

from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger
from app.database.models.task import Task
from app.database.postgres import SessionLocal

DATA_DIR = "data/meetings"
os.makedirs(DATA_DIR, exist_ok=True)
INDEX_FILE = os.path.join(DATA_DIR, "meetings_index.json")


@dataclass
class MeetingRecord:
    meeting_id: str
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: float = 0.0
    status: str = "recording"
    transcript: str = ""
    structured_notes: Optional[Dict[str, Any]] = None
    auto_tasks_created: List[str] = field(default_factory=list)
    audio_path: Optional[str] = None


class MeetingIntelligence:
    def __init__(self):
        self.meetings: Dict[str, MeetingRecord] = {}
        self.active_recordings: Dict[str, bool] = {}
        self._load_index()

    def _load_index(self):
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        v["started_at"] = datetime.fromisoformat(v["started_at"])
                        if v.get("ended_at"):
                            v["ended_at"] = datetime.fromisoformat(v["ended_at"])
                        self.meetings[k] = MeetingRecord(**v)
            except Exception as e:
                logger.error(f"Failed to load meeting index: {e}")

    def _save_index(self):
        try:
            data = {}
            for k, v in self.meetings.items():
                record_dict = asdict(v)
                record_dict["started_at"] = record_dict["started_at"].isoformat()
                if record_dict["ended_at"]:
                    record_dict["ended_at"] = record_dict["ended_at"].isoformat()
                data[k] = record_dict
            with open(INDEX_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save meeting index: {e}")

    def start_recording(self, title: str = "Untitled Meeting") -> MeetingRecord:
        meeting_id = str(uuid.uuid4())
        audio_path = os.path.join(DATA_DIR, f"{meeting_id}.wav")
        
        record = MeetingRecord(
            meeting_id=meeting_id,
            title=title,
            started_at=datetime.utcnow(),
            audio_path=audio_path
        )
        
        try:
            sd.default.device  # Test if sounddevice is available
            self.active_recordings[meeting_id] = True
            
            # Start background recording task
            asyncio.create_task(self._record_audio_task(meeting_id, audio_path))
        except Exception as e:
            logger.warning(f"Sounddevice not available, simulating recording: {e}")
            record.status = "recording_simulated"

        self.meetings[meeting_id] = record
        self._save_index()
        return record

    async def _record_audio_task(self, meeting_id: str, audio_path: str):
        sample_rate = 44100
        channels = 1
        frames = []

        try:
            def callback(indata, frames_count, time_info, status):
                if status:
                    logger.warning(f"Audio recording status: {status}")
                if self.active_recordings.get(meeting_id):
                    frames.append(indata.copy())
                else:
                    raise sd.CallbackStop()

            with sd.InputStream(samplerate=sample_rate, channels=channels, callback=callback):
                while self.active_recordings.get(meeting_id):
                    await asyncio.sleep(0.1)

            if frames:
                import numpy as np
                audio_data = np.concatenate(frames, axis=0)
                audio_data = (audio_data * 32767).astype(np.int16)
                
                with wave.open(audio_path, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data.tobytes())
                    
        except Exception as e:
            logger.error(f"Recording error for {meeting_id}: {e}")
            if meeting_id in self.meetings:
                self.meetings[meeting_id].status = "failed"
                self._save_index()

    def stop_recording(self, meeting_id: str) -> MeetingRecord:
        record = self.meetings.get(meeting_id)
        if not record:
            raise ValueError("Meeting not found")

        if record.status in ["recording", "recording_simulated"]:
            self.active_recordings[meeting_id] = False
            record.ended_at = datetime.utcnow()
            record.duration_minutes = (record.ended_at - record.started_at).total_seconds() / 60.0
            record.status = "processing"
            self._save_index()

            # Start processing pipeline in background
            asyncio.create_task(self._process_meeting(meeting_id))
            
        return record

    async def _process_meeting(self, meeting_id: str):
        record = self.meetings.get(meeting_id)
        if not record:
            return

        try:
            if record.audio_path and os.path.exists(record.audio_path):
                transcript = self._transcribe(record.audio_path)
            else:
                transcript = "[Simulated transcript or audio missing]"
            
            record.transcript = transcript
            record.structured_notes = await self._generate_structured_notes(transcript)
            
            if record.structured_notes and "action_items" in record.structured_notes:
                self._create_tasks_from_actions(meeting_id, record.structured_notes["action_items"])
            
            record.status = "completed"
        except Exception as e:
            logger.error(f"Meeting processing failed for {meeting_id}: {e}")
            record.status = "failed"
            
        self._save_index()

    def _transcribe(self, audio_path: str) -> str:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, beam_size=5)
            return " ".join([segment.text for segment in segments])
        except ImportError:
            try:
                import whisper
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                return result["text"]
            except ImportError:
                return "[Transcription unavailable — install faster-whisper or openai-whisper]"
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "[Transcription failed]"

    async def _generate_structured_notes(self, transcript: str) -> Dict[str, Any]:
        if not transcript or transcript.startswith("["):
            return {
                "summary": "No transcript available.",
                "decisions": [],
                "action_items": [],
                "open_questions": [],
                "key_quotes": []
            }
            
        prompt = f"""
Analyze the following meeting transcript and extract structured information.
Respond ONLY with a JSON object matching this schema:
{{
    "summary": "Brief 2-3 sentence summary",
    "decisions": ["Decision 1", "Decision 2"],
    "action_items": [{{"task": "...", "assignee": "...", "deadline": "..."}}],
    "open_questions": ["Question 1"],
    "key_quotes": ["Important quote 1"]
}}

Transcript:
{transcript}
"""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            is_avail = await ollama_client.is_available()
            if is_avail:
                response = await ollama_client.chat(messages=messages, model="deepseek-r1:latest")
                # Attempt to parse json from response
                content = response.get("message", {}).get("content", "")
                # naive extraction if wrapped in code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                return json.loads(content)
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            
        # Fallback basic extraction
        sentences = transcript.split(". ")
        actions = []
        for s in sentences:
            s_lower = s.lower()
            if any(word in s_lower for word in ["will", "need to", "should", "must", "action"]):
                actions.append({"task": s, "assignee": "Unassigned", "deadline": "TBD"})
                
        return {
            "summary": "Basic summary generated locally.",
            "decisions": [],
            "action_items": actions,
            "open_questions": [],
            "key_quotes": []
        }

    def _create_tasks_from_actions(self, meeting_id: str, action_items: List[Dict[str, str]]):
        record = self.meetings.get(meeting_id)
        if not record:
            return

        db = SessionLocal()
        try:
            for item in action_items:
                task_title = item.get("task", "Unknown Task")
                new_task = Task(
                    title=task_title,
                    project="Meetings",
                    priority="medium",
                    status="inbox"
                )
                db.add(new_task)
                db.commit()
                db.refresh(new_task)
                record.auto_tasks_created.append(str(new_task.id))
        except Exception as e:
            logger.error(f"Failed to create tasks from actions: {e}")
            db.rollback()
        finally:
            db.close()

    def get_meeting(self, meeting_id: str) -> Optional[MeetingRecord]:
        return self.meetings.get(meeting_id)

    def list_meetings(self, limit: int = 20) -> List[MeetingRecord]:
        sorted_meetings = sorted(
            self.meetings.values(), 
            key=lambda x: x.started_at, 
            reverse=True
        )
        return sorted_meetings[:limit]

meeting_intelligence = MeetingIntelligence()
