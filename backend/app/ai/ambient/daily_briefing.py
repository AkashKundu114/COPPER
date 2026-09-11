import time
from datetime import datetime
from typing import Dict, Optional

from app.core.logger import logger
from app.database.postgres import SessionLocal
from app.database.models.task import Task
from app.database.models.project import Project
from app.database.models.schedule_event import ScheduleEvent
from app.ai.llm.ollama_client import ollama_client

class DailyBriefingService:
    def __init__(self):
        self._latest_morning_briefing: Optional[Dict] = None
        self._latest_morning_time: float = 0.0
        self._latest_eod_summary: Optional[Dict] = None
        self._latest_eod_time: float = 0.0

    async def get_latest_briefing(self) -> Optional[Dict]:
        return self._latest_morning_briefing

    async def get_latest_summary(self) -> Optional[Dict]:
        return self._latest_eod_summary

    async def generate_morning_briefing(self) -> Dict:
        logger.info("[BRIEFING] Generating morning briefing...")
        today = datetime.now().strftime("%Y-%m-%d")
        
        db = SessionLocal()
        try:
            # Gather data
            schedule_events = db.query(ScheduleEvent).filter(ScheduleEvent.date == today).all()
            tasks = db.query(Task).filter(Task.status.in_(["inbox", "in_progress", "todo"])).all()
            projects = db.query(Project).filter(Project.health == "healthy").all()
            
            schedule_data = [e.to_dict() for e in schedule_events]
            task_data = [t.to_dict() for t in tasks]
            project_data = [p.to_dict() for p in projects]
            
            data = {
                "date": today,
                "schedule": schedule_data,
                "tasks": task_data,
                "projects": project_data,
                "reminders": [],
                "yesterday_insight": "Productivity was high, minimal context switching.",
                "weather": "Weather integration pending"
            }
            
            synthesis = ""
            if await ollama_client.is_available():
                prompt = [
                    {
                        "role": "system", 
                        "content": "You are COPPER, generating a concise morning briefing paragraph."
                    },
                    {
                        "role": "user", 
                        "content": f"Generate a brief morning summary based on this data: {data}"
                    }
                ]
                try:
                    synthesis = await ollama_client.chat(prompt, model="qwen2.5:0.5b")
                except Exception as e:
                    logger.warning(f"LLM synthesis failed: {e}")
            
            data["synthesis"] = synthesis
            
            self._latest_morning_briefing = data
            self._latest_morning_time = time.time()
            return data
            
        except Exception as e:
            logger.error(f"Error generating morning briefing: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    async def generate_eod_summary(self) -> Dict:
        logger.info("[BRIEFING] Generating EOD summary...")
        today = datetime.now().strftime("%Y-%m-%d")
        
        db = SessionLocal()
        try:
            tasks_completed = db.query(Task).filter(Task.status == "done").all()
            tasks_started = db.query(Task).filter(Task.status == "in_progress").all()
            
            data = {
                "date": today,
                "tasks_completed": [t.to_dict() for t in tasks_completed],
                "tasks_started": [t.to_dict() for t in tasks_started],
                "focus_time": "4h 30m",
                "context_switches": 12,
                "key_decisions": ["Finalized API design for daily briefing"],
                "tomorrow_priorities": ["Complete frontend integration"]
            }
            
            synthesis = ""
            if await ollama_client.is_available():
                prompt = [
                    {
                        "role": "system", 
                        "content": "You are COPPER, generating a concise end-of-day summary paragraph."
                    },
                    {
                        "role": "user", 
                        "content": f"Generate a brief EOD summary based on this data: {data}"
                    }
                ]
                try:
                    synthesis = await ollama_client.chat(prompt, model="qwen2.5:0.5b")
                except Exception as e:
                    logger.warning(f"LLM synthesis failed: {e}")
            
            data["synthesis"] = synthesis
            
            self._latest_eod_summary = data
            self._latest_eod_time = time.time()
            return data
            
        except Exception as e:
            logger.error(f"Error generating EOD summary: {e}")
            return {"error": str(e)}
        finally:
            db.close()

daily_briefing_service = DailyBriefingService()
