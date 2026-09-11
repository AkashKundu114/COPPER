import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from app.core.logger import logger

@dataclass
class Commitment:
    commitment_id: str
    title: str
    deadline: str
    status: str
    urgency: str
    nudges_sent: int
    created_at: str
    completed_at: str | None

class AccountabilityTracker:
    def __init__(self, filepath="data/commitments.json"):
        self.filepath = Path(filepath)
        self.commitments: list[Commitment] = []
        self._load()

    def _load(self):
        try:
            if self.filepath.exists():
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.commitments = [Commitment(**item) for item in data]
        except Exception as e:
            logger.error(f"Failed to load commitments: {e}")
            self.commitments = []

    def _save(self):
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w") as f:
                json.dump([asdict(c) for c in self.commitments], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save commitments: {e}")

    def add_commitment(self, title: str, deadline: str, urgency: str = "medium") -> Commitment:
        now = datetime.now(timezone.utc).isoformat()
        commitment = Commitment(
            commitment_id=str(uuid.uuid4()),
            title=title,
            deadline=deadline,
            status="pending",
            urgency=urgency,
            nudges_sent=0,
            created_at=now,
            completed_at=None
        )
        self.commitments.append(commitment)
        self._save()
        return commitment

    def fulfill_commitment(self, commitment_id: str) -> Commitment | None:
        for c in self.commitments:
            if c.commitment_id == commitment_id:
                c.status = "fulfilled"
                c.completed_at = datetime.now(timezone.utc).isoformat()
                self._save()
                return c
        return None

    def check_overdue_commitments(self) -> list[dict]:
        nudges = []
        now = datetime.now(timezone.utc)
        for c in self.commitments:
            if c.status == "pending":
                try:
                    deadline_dt = datetime.fromisoformat(c.deadline.replace('Z', '+00:00'))
                    if now > deadline_dt:
                        c.nudges_sent += 1
                        nudge_msg = f"Gentle reminder: '{c.title}' is overdue!" if c.urgency == "low" else f"Firm nudge: You missed the deadline for '{c.title}'. Please complete it!"
                        nudges.append({"commitment_id": c.commitment_id, "message": nudge_msg})
                except Exception as e:
                    logger.error(f"Error parsing deadline for {c.commitment_id}: {e}")
        
        if nudges:
            self._save()
        return nudges

    def get_accountability_report(self) -> dict:
        total = len(self.commitments)
        fulfilled = sum(1 for c in self.commitments if c.status == "fulfilled")
        follow_through_rate_pct = (fulfilled / total * 100) if total > 0 else 0.0
        
        return {
            "total_commitments": total,
            "fulfilled": fulfilled,
            "follow_through_rate_pct": follow_through_rate_pct,
            "current_streak": 0,  # placeholder
            "active_nudges": sum(c.nudges_sent for c in self.commitments if c.status == "pending")
        }

accountability_tracker = AccountabilityTracker()
