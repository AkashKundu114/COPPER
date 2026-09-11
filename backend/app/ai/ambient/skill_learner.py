import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from uuid import uuid4
import re
from typing import Optional

from app.core.logger import logger

@dataclass
class LearnedSkill:
    skill_id: str
    name: str
    description: str
    steps: list[dict]
    input_params: list[dict]
    output_format: str
    created_at: datetime
    last_used: datetime | None = None
    use_count: int = 0
    success_count: int = 0
    success_rate: float = 1.0
    avg_duration_seconds: float = 0.0
    tags: list[str] = field(default_factory=list)
    source_task: str = ""

    def to_dict(self):
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        if self.last_used:
            d["last_used"] = self.last_used.isoformat()
        return d

    @classmethod
    def from_dict(cls, data):
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "last_used" in data and data["last_used"] is not None and isinstance(data["last_used"], str):
            data["last_used"] = datetime.fromisoformat(data["last_used"])
        return cls(**data)


class SkillLearner:
    def __init__(self, data_path: str = "data/learned_skills.json"):
        self.data_path = data_path
        self.skills: dict[str, LearnedSkill] = {}
        self._load_skills()

    def _load_skills(self):
        if not os.path.exists(self.data_path):
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            self._save_skills()
            return
        
        try:
            with open(self.data_path, "r") as f:
                data = json.load(f)
                for skill_data in data:
                    skill = LearnedSkill.from_dict(skill_data)
                    self.skills[skill.skill_id] = skill
        except Exception as e:
            logger.error(f"Failed to load skills: {e}")

    def _save_skills(self):
        try:
            with open(self.data_path, "w") as f:
                json.dump([s.to_dict() for s in self.skills.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save skills: {e}")

    def _generate_name(self, description: str) -> str:
        words = re.sub(r'[^a-zA-Z0-9\s]', '', description.lower()).split()
        return "_".join(words[:5])

    def extract_skill(self, task_description: str, steps_executed: list[dict], result: dict) -> LearnedSkill:
        name = self._generate_name(task_description)
        
        # Simple extraction logic: find input_params based on common variations
        # In a real system, we'd use LLM to generalize the task steps
        # For now, create a basic templatization
        
        input_params = []
        # Mock parameter extraction, just add a generic 'input_data' if steps are empty or use dummy logic
        
        skill = LearnedSkill(
            skill_id=str(uuid4()),
            name=name,
            description=f"Skill extracted from: {task_description}",
            steps=steps_executed,
            input_params=input_params,
            output_format="dict",
            created_at=datetime.utcnow(),
            source_task=task_description
        )
        
        self.skills[skill.skill_id] = skill
        self._save_skills()
        logger.info(f"Skill '{name}' extracted and saved with ID {skill.skill_id}")
        return skill

    def find_matching_skill(self, task_description: str) -> Optional[LearnedSkill]:
        if not self.skills:
            return None
            
        desc_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', task_description.lower()).split())
        
        best_match = None
        best_score = 0.0
        
        for skill in self.skills.values():
            skill_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', skill.description.lower()).split())
            if not skill_words or not desc_words:
                continue
                
            intersection = len(desc_words.intersection(skill_words))
            union = len(desc_words.union(skill_words))
            score = intersection / union
            
            if score > best_score and score > 0.4:
                best_score = score
                best_match = skill
                
        return best_match

    async def execute_skill(self, skill_id: str, params: dict) -> dict:
        if skill_id not in self.skills:
            raise ValueError(f"Skill {skill_id} not found")
            
        skill = self.skills[skill_id]
        start_time = time.time()
        
        try:
            logger.info(f"Executing skill {skill.name} ({skill_id}) with params {params}")
            
            # Execute each step - this would ideally integrate with workflow_engine.py
            # For this simplified version, we just mock successful execution
            
            duration = time.time() - start_time
            total_duration = skill.avg_duration_seconds * skill.success_count
            skill.use_count += 1
            skill.success_count += 1
            skill.success_rate = skill.success_count / skill.use_count
            skill.avg_duration_seconds = (total_duration + duration) / skill.success_count
            skill.last_used = datetime.now(timezone.utc)
            
            result = {
                "status": "success",
                "skill_id": skill_id,
                "executed_steps": len(skill.steps),
                "use_count": skill.use_count,
                "duration_seconds": round(duration, 3),
            }

            self._save_skills()
            return result
            
        except Exception as e:
            skill.use_count += 1
            skill.success_rate = skill.success_count / skill.use_count
            skill.last_used = datetime.now(timezone.utc)
            self._save_skills()
            raise e

    def list_skills(self, tag: Optional[str] = None) -> list[LearnedSkill]:
        if tag:
            return [s for s in self.skills.values() if tag in s.tags]
        return list(self.skills.values())

    def get_skill(self, skill_id: str) -> Optional[LearnedSkill]:
        return self.skills.get(skill_id)

    def delete_skill(self, skill_id: str) -> bool:
        if skill_id in self.skills:
            del self.skills[skill_id]
            self._save_skills()
            return True
        return False

    def get_stats(self) -> dict:
        total = len(self.skills)
        if total == 0:
            return {
                "total_skills": 0,
                "total_uses": 0,
                "avg_success_rate": 0.0,
                "most_used_skill": None
            }
            
        uses = sum(s.use_count for s in self.skills.values())
        avg_success = sum(s.success_rate for s in self.skills.values()) / total
        most_used = max(self.skills.values(), key=lambda x: x.use_count)
        
        return {
            "total_skills": total,
            "total_uses": uses,
            "avg_success_rate": avg_success,
            "most_used_skill": most_used.name if most_used else None
        }

skill_learner = SkillLearner()
