import os
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Optional

from app.core.logger import logger

@dataclass
class SkillGap:
    gap_id: str
    topic: str
    query_count: int
    first_observed: str
    last_observed: str
    recommended_guide: Optional[str]
    difficulty_level: str
    status: str


class SkillGapDetector:
    def __init__(self):
        self.data_file = "data/skill_gaps.json"
        self._ensure_data_dir()
        self.gaps: dict[str, SkillGap] = {}
        self._load()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

    def _load(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                for item in data:
                    self.gaps[item["topic"].lower()] = SkillGap(**item)
        except Exception as e:
            logger.error(f"Failed to load skill gaps: {e}")

    def _save(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump([asdict(g) for g in self.gaps.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save skill gaps: {e}")

    def record_query_topic(self, topic: str):
        now = datetime.now(timezone.utc).isoformat()
        key = topic.lower()
        if key in self.gaps:
            gap = self.gaps[key]
            gap.query_count += 1
            gap.last_observed = now
        else:
            gap = SkillGap(
                gap_id=str(uuid.uuid4()),
                topic=topic,
                query_count=1,
                first_observed=now,
                last_observed=now,
                recommended_guide=None,
                difficulty_level="beginner",
                status="detected"
            )
            self.gaps[key] = gap

        if gap.query_count >= 3 and not gap.recommended_guide:
            gap.recommended_guide = f"Tutorial outline for {gap.topic}: 1. Basics 2. Intermediate concepts 3. Advanced usage"
            logger.info(f"Generated guide for {gap.topic}")

        self._save()

    def get_active_gaps(self) -> List[SkillGap]:
        return list(self.gaps.values())

    def mark_gap_status(self, gap_id: str, status: str):
        for gap in self.gaps.values():
            if gap.gap_id == gap_id:
                gap.status = status
                self._save()
                return True
        return False

skill_gap_detector = SkillGapDetector()
