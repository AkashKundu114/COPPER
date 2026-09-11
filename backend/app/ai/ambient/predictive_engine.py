import os
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy import select

from app.core.logger import logger
from app.database.postgres import SessionLocal
from app.database.models.task import Task

@dataclass
class PredictedTask:
    prediction_id: str
    title: str
    confidence: float
    predicted_time: str
    pattern_source: str
    prepared_result: Optional[dict] = None
    status: str = "pending"

class PredictiveEngine:
    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.predictions_file = os.path.join(self.data_dir, "predictions.json")
        self.history_file = os.path.join(self.data_dir, "pattern_history.json")
        self._predictions: list[PredictedTask] = self._load_predictions()
        
    def _load_predictions(self) -> list[PredictedTask]:
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, "r") as f:
                    data = json.load(f)
                    return [PredictedTask(**item) for item in data]
            except Exception as e:
                logger.error(f"Failed to load predictions: {e}")
        return []

    def _save_predictions(self):
        try:
            with open(self.predictions_file, "w") as f:
                json.dump([asdict(p) for p in self._predictions], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save predictions: {e}")

    def _fuzzy_title_match(self, title1: str, title2: str) -> bool:
        t1_words = title1.lower().split()[:3]
        t2_words = title2.lower().split()[:3]
        return t1_words == t2_words and len(t1_words) > 0

    def analyze_patterns(self) -> list[PredictedTask]:
        try:
            now = datetime.now(UTC)
            thirty_days_ago = now - timedelta(days=30)
            
            with SessionLocal() as session:
                tasks = session.query(Task).filter(
                    Task.created_at >= thirty_days_ago,
                    Task.status == "completed"
                ).all()

            from collections import defaultdict
            dow_tasks = defaultdict(list)
            
            for task in tasks:
                if task.created_at:
                    dow = task.created_at.weekday()
                    dow_tasks[dow].append(task)
            
            new_predictions = []
            
            for offset in range(7):
                target_date = now + timedelta(days=offset)
                target_dow = target_date.weekday()
                
                tasks_for_dow = dow_tasks.get(target_dow, [])
                if not tasks_for_dow:
                    continue
                    
                matched_groups = []
                processed = set()
                
                for i, t1 in enumerate(tasks_for_dow):
                    if i in processed:
                        continue
                    current_group = [t1]
                    for j, t2 in enumerate(tasks_for_dow[i+1:], start=i+1):
                        if j not in processed and self._fuzzy_title_match(t1.title, t2.title):
                            current_group.append(t2)
                            processed.add(j)
                    
                    if len(current_group) >= 3:
                        matched_groups.append(current_group)
                        
                for group in matched_groups:
                    avg_hour = int(sum(t.created_at.hour for t in group) / len(group))
                    
                    target_time = target_date.replace(hour=avg_hour, minute=0, second=0, microsecond=0)
                    
                    if target_time > now:
                        prediction = PredictedTask(
                            prediction_id=str(uuid.uuid4()),
                            title=group[0].title,
                            confidence=min(1.0, 0.5 + (len(group) * 0.1)),
                            predicted_time=target_time.strftime("%A %H:00"),
                            pattern_source="recurring_task"
                        )
                        new_predictions.append(prediction)
            
            existing_pending = [p for p in self._predictions if p.status == "pending"]
            final_predictions = existing_pending
            for np in new_predictions:
                if not any(self._fuzzy_title_match(np.title, ep.title) for ep in final_predictions):
                    final_predictions.append(np)
                    
            self._predictions = final_predictions
            self._save_predictions()
            
            # Save history
            try:
                history_data = {"last_analyzed": now.isoformat(), "patterns_found": len(new_predictions)}
                with open(self.history_file, "w") as f:
                    json.dump(history_data, f)
            except Exception as e:
                logger.error(f"Failed to save pattern history: {e}")
                
            return new_predictions
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return []

    def get_predictions_for_today(self) -> list[PredictedTask]:
        now = datetime.now(UTC)
        today_str = now.strftime("%A")
        
        today_predictions = [
            p for p in self._predictions 
            if p.status == "pending" and p.predicted_time.startswith(today_str)
        ]
        return today_predictions

    def mark_prediction(self, prediction_id: str, status: str):
        for p in self._predictions:
            if p.prediction_id == prediction_id:
                p.status = status
                break
        self._save_predictions()
        
    def get_all_patterns(self) -> list[dict]:
        return [asdict(p) for p in self._predictions]

predictive_engine = PredictiveEngine()
