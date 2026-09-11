import json
import os
from dataclasses import asdict, dataclass
from typing import List, Optional

from app.core.logger import logger


@dataclass
class SessionHandoff:
    session_id: str
    timestamp: str
    active_project: str
    key_decisions: List[str]
    unresolved_topics: List[str]
    suggested_next_steps: List[str]
    summary: str


class ContextContinuityManager:
    def __init__(self, storage_path: str = "data/session_handoffs.json"):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_handoffs(self) -> List[SessionHandoff]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [SessionHandoff(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading session handoffs: {e}")
            return []

    def _save_handoffs(self, handoffs: List[SessionHandoff]):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([asdict(h) for h in handoffs], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session handoffs: {e}")

    def create_handoff(
        self,
        session_id: str,
        project: str,
        decisions: List[str],
        topics: List[str],
        next_steps: List[str],
        summary: str,
    ) -> SessionHandoff:
        from datetime import datetime

        timestamp = datetime.utcnow().isoformat()
        handoff = SessionHandoff(
            session_id=session_id,
            timestamp=timestamp,
            active_project=project,
            key_decisions=decisions,
            unresolved_topics=topics,
            suggested_next_steps=next_steps,
            summary=summary,
        )

        handoffs = self._load_handoffs()
        handoffs.append(handoff)
        self._save_handoffs(handoffs)
        logger.info(f"Created session handoff for session {session_id}")
        return handoff

    def get_latest_handoff(self, project: Optional[str] = None) -> Optional[SessionHandoff]:
        handoffs = self._load_handoffs()
        if not handoffs:
            return None

        if project:
            filtered = [h for h in handoffs if h.active_project == project]
            if filtered:
                return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[0]
            return None
        
        return sorted(handoffs, key=lambda x: x.timestamp, reverse=True)[0]

    def generate_resume_prompt(self) -> str:
        handoff = self.get_latest_handoff()
        if not handoff:
            return "No previous session data found. How can I help you today?"
            
        decisions_str = ", ".join(handoff.key_decisions) if handoff.key_decisions else "nothing major"
        next_steps_str = ", ".join(handoff.suggested_next_steps) if handoff.suggested_next_steps else "explore further"
        
        return f"Last time we worked on {handoff.active_project}. We decided {decisions_str} and were planning to {next_steps_str}. Ready to continue?"


context_continuity = ContextContinuityManager()
