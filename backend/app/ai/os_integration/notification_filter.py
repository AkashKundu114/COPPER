import json
import uuid
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

from app.core.logger import logger
from app.ai.ambient.cognitive_load import cognitive_load_detector

DATA_FILE = "data/notifications.json"

@dataclass
class IncomingNotification:
    id: str
    source: str
    title: str
    message: str
    timestamp: str
    category: str  # "urgent" | "batchable" | "fyi"
    status: str    # "unread" | "suppressed" | "delivered" | "digested"

class NotificationFilter:
    def __init__(self, data_file: str = DATA_FILE):
        self.data_file = data_file
        self.notifications: List[IncomingNotification] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.notifications = [IncomingNotification(**n) for n in data]
        except Exception as e:
            logger.error(f"Failed to load notifications: {e}")
            self.notifications = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w") as f:
                json.dump([asdict(n) for n in self.notifications], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save notifications: {e}")

    def _classify_urgency(self, source: str, title: str, message: str) -> str:
        text = f"{source} {title} {message}".lower()
        urgent_keywords = ["urgent", "error", "fail", "critical", "alert", "immediate"]
        if any(k in text for k in urgent_keywords):
            return "urgent"
        
        batchable_keywords = ["update", "digest", "newsletter", "sync", "info"]
        if any(k in text for k in batchable_keywords):
            return "batchable"
            
        return "fyi"

    def post_notification(self, source: str, title: str, message: str) -> IncomingNotification:
        category = self._classify_urgency(source, title, message)
        
        status = "unread"
        if cognitive_load_detector.should_suppress_notifications() and category != "urgent":
            status = "suppressed"
            
        notif = IncomingNotification(
            id=str(uuid.uuid4()),
            source=source,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            category=category,
            status=status
        )
        self.notifications.append(notif)
        self._save()
        return notif

    def get_notifications(self, status: Optional[str] = None) -> List[IncomingNotification]:
        if status:
            return [n for n in self.notifications if n.status == status]
        return self.notifications

    def generate_digest(self) -> dict:
        unread = self.get_notifications(status="unread")
        suppressed = self.get_notifications(status="suppressed")
        
        # Combine both for digest
        targets = unread + suppressed
        
        urgent_count = len([n for n in targets if n.category == "urgent"])
        batchable_count = len([n for n in targets if n.category == "batchable"])
        fyi_count = len([n for n in targets if n.category == "fyi"])
        
        total = urgent_count + batchable_count + fyi_count
        
        if total == 0:
            summary = "No new notifications."
        else:
            summary = f"You have {total} unread alerts ({urgent_count} urgent, {batchable_count} batchable, {fyi_count} fyi)."
            
        for n in targets:
            n.status = "digested"
        self._save()
            
        return {
            "summary": summary,
            "counts": {
                "urgent": urgent_count,
                "batchable": batchable_count,
                "fyi": fyi_count,
                "total": total
            }
        }

    def mark_delivered(self, id: str):
        for n in self.notifications:
            if n.id == id:
                n.status = "delivered"
                break
        self._save()

notification_filter = NotificationFilter()
