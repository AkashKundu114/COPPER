import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

from app.core.logger import logger
from app.ai.ambient.context_watcher import context_watcher
from app.api.websocket.manager import manager


class CognitiveState(str, Enum):
    DEEP_FOCUS = "deep_focus"
    NORMAL_FLOW = "normal_flow"
    CONTEXT_SWITCHING = "context_switching"
    STRESSED = "stressed"
    IDLE = "idle"


@dataclass
class CognitiveProfile:
    state: CognitiveState
    confidence: float
    window_switch_rate: float
    avg_session_duration: float
    current_focus_streak: float
    recommendations: list[str]
    detected_at: datetime


class CognitiveLoadDetector:
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.history: List[CognitiveProfile] = []
        self.history_size = 720  # 24 hours at 2-min intervals
        self.poll_interval = 120.0  # 2 minutes
        self.current_state = CognitiveState.IDLE

    def start(self):
        if not self.is_running:
            self.is_running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._detection_loop())
                logger.info("Cognitive Load Detector started.")
            except RuntimeError:
                logger.warning("Cognitive Load Detector could not start: no running event loop.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self._task:
                self._task.cancel()
            logger.info("Cognitive Load Detector stopped.")

    def get_recommendations(self, state: CognitiveState) -> list[str]:
        if state == CognitiveState.DEEP_FOCUS:
            return ["Suppress non-urgent notifications", "Queue clipboard processing", "Protect flow state"]
        elif state == CognitiveState.NORMAL_FLOW:
            return ["Standard notification delivery", "Process clipboard normally"]
        elif state == CognitiveState.CONTEXT_SWITCHING:
            return ["Offer to help organize/prioritize", "Suggest parking current context", "Show active project list"]
        elif state == CognitiveState.STRESSED:
            return ["Use shorter, more concise responses", "Proactively offer to take over tasks", "Break complex requests into steps"]
        elif state == CognitiveState.IDLE:
            return ["Surface learning opportunities", "Show background research results", "Suggest reviewing pending tasks"]
        return []

    def detect_state(self) -> CognitiveProfile:
        entries = context_watcher.get_timeline(hours=1/6.0)  # Last 10 minutes
        
        now = datetime.now()
        
        # IDLE check: no activity entries in last 5 minutes
        five_mins_ago = now - timedelta(minutes=5)
        recent_activity = [e for e in entries if e.timestamp >= five_mins_ago]
        if not recent_activity:
            return CognitiveProfile(
                state=CognitiveState.IDLE,
                confidence=1.0,
                window_switch_rate=0.0,
                avg_session_duration=0.0,
                current_focus_streak=0.0,
                recommendations=self.get_recommendations(CognitiveState.IDLE),
                detected_at=now
            )
            
        confidence = min(len(entries) / 120.0, 1.0)
        
        switches = 0
        current_focus_streak_mins = 0.0
        avg_session_seconds = 0.0
        
        if entries:
            current_app = entries[0].app_name
            current_window = entries[0].window_title
            
            session_durations = []
            current_session_start = entries[0].timestamp
            last_timestamp = entries[0].timestamp
            
            for i in range(1, len(entries)):
                e = entries[i]
                if e.app_name != current_app or e.window_title != current_window:
                    switches += 1
                    session_durations.append((last_timestamp - current_session_start).total_seconds() + context_watcher.poll_interval)
                    current_app = e.app_name
                    current_window = e.window_title
                    current_session_start = e.timestamp
                last_timestamp = e.timestamp
                
            session_durations.append((last_timestamp - current_session_start).total_seconds() + context_watcher.poll_interval)
            
            if session_durations:
                avg_session_seconds = sum(session_durations) / len(session_durations)
        
        sessions = context_watcher.get_sessions(hours=2)
        if sessions:
            last_session = sessions[-1]
            current_focus_streak_mins = last_session.duration_minutes
        elif entries:
            current_focus_streak_mins = (now - entries[-1].timestamp).total_seconds() / 60.0

        window_switch_rate = switches / 10.0  # Last 10 minutes

        state = CognitiveState.NORMAL_FLOW
        
        if window_switch_rate > 4 or (avg_session_seconds > 0 and avg_session_seconds < 15):
            state = CognitiveState.STRESSED
        elif window_switch_rate >= 2:
            state = CognitiveState.CONTEXT_SWITCHING
        elif window_switch_rate <= 0.5 and current_focus_streak_mins > 15:
            state = CognitiveState.DEEP_FOCUS
            
        return CognitiveProfile(
            state=state,
            confidence=confidence,
            window_switch_rate=window_switch_rate,
            avg_session_duration=avg_session_seconds,
            current_focus_streak=current_focus_streak_mins,
            recommendations=self.get_recommendations(state),
            detected_at=now
        )

    async def _detection_loop(self):
        while self.is_running:
            try:
                profile = self.detect_state()
                self.history.append(profile)
                if len(self.history) > self.history_size:
                    self.history.pop(0)

                if profile.state != self.current_state:
                    self.current_state = profile.state
                    await manager.broadcast_alert({
                        "type": "cognitive_state_change",
                        "new_state": profile.state.value,
                        "confidence": profile.confidence,
                        "recommendations": profile.recommendations,
                        "detected_at": profile.detected_at.isoformat()
                    })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cognitive Load Detector loop error: {e}")

            await asyncio.sleep(self.poll_interval)

    def get_history(self, hours: int = 24) -> List[CognitiveProfile]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [p for p in self.history if p.detected_at >= cutoff]

    def should_suppress_notifications(self) -> bool:
        if not self.history:
            return False
        return self.history[-1].state == CognitiveState.DEEP_FOCUS


cognitive_load_detector = CognitiveLoadDetector()
