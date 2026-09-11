import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.logger import logger
from app.ai.ambient.context_watcher import context_watcher
from app.ai.memory.persistent_memory import persistent_memory

@dataclass
class ProjectContext:
    project_name: str
    last_active: datetime
    active_files: list[str] = field(default_factory=list)
    recent_topics: list[str] = field(default_factory=list)
    pending_tasks: list[dict] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    parked_at: Optional[datetime] = None
    summary: str = ""

    def to_dict(self):
        d = asdict(self)
        d['last_active'] = self.last_active.isoformat()
        if self.parked_at:
            d['parked_at'] = self.parked_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict):
        last_active = datetime.fromisoformat(data['last_active'])
        parked_at = datetime.fromisoformat(data['parked_at']) if data.get('parked_at') else None
        return cls(
            project_name=data['project_name'],
            last_active=last_active,
            active_files=data.get('active_files', []),
            recent_topics=data.get('recent_topics', []),
            pending_tasks=data.get('pending_tasks', []),
            session_ids=data.get('session_ids', []),
            parked_at=parked_at,
            summary=data.get('summary', "")
        )

class ContextSwitcher:
    def __init__(self):
        self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
        self.patterns_path = os.path.join(self.data_dir, "project_patterns.json")
        self.contexts_path = os.path.join(self.data_dir, "project_contexts.json")
        
        self.patterns: Dict[str, List[str]] = self._load_patterns()
        self.contexts: Dict[str, ProjectContext] = self._load_contexts()
        self.current_project: Optional[str] = None

    def _load_patterns(self) -> Dict[str, List[str]]:
        if not os.path.exists(self.patterns_path):
            os.makedirs(os.path.dirname(self.patterns_path), exist_ok=True)
            default_patterns = {
                "COPPER": ["C.O.P.P.E.R", "copper"],
                "Portfolio": ["portfolio", "resume"],
                "General": []
            }
            with open(self.patterns_path, "w", encoding="utf-8") as f:
                json.dump(default_patterns, f, indent=4)
            return default_patterns
            
        try:
            with open(self.patterns_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load project patterns: {e}")
            return {}

    def _load_contexts(self) -> Dict[str, ProjectContext]:
        if not os.path.exists(self.contexts_path):
            return {}
        try:
            with open(self.contexts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: ProjectContext.from_dict(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load project contexts: {e}")
            return {}

    def _save_contexts(self):
        try:
            with open(self.contexts_path, "w", encoding="utf-8") as f:
                data = {k: v.to_dict() for k, v in self.contexts.items()}
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save project contexts: {e}")

    def detect_project_switch(self, current_app: str, current_title: str) -> Optional[str]:
        title_lower = current_title.lower()
        
        for project, keywords in self.patterns.items():
            for kw in keywords:
                if kw.lower() in title_lower:
                    if self.current_project != project:
                        logger.info(f"Detected project switch to {project} based on window: {current_title}")
                        self.current_project = project
                        if project not in self.contexts:
                            self.contexts[project] = ProjectContext(project_name=project, last_active=datetime.now())
                        else:
                            self.contexts[project].last_active = datetime.now()
                            self.contexts[project].parked_at = None
                        self._save_contexts()
                    return project
        return None

    def switch_to(self, project_name: str) -> ProjectContext:
        self.current_project = project_name
        if project_name not in self.contexts:
            self.contexts[project_name] = ProjectContext(
                project_name=project_name, 
                last_active=datetime.now()
            )
        else:
            self.contexts[project_name].last_active = datetime.now()
            self.contexts[project_name].parked_at = None
            
        self._save_contexts()
        return self.contexts[project_name]

    def park_current(self) -> Optional[ProjectContext]:
        if not self.current_project or self.current_project not in self.contexts:
            return None
            
        context = self.contexts[self.current_project]
        context.parked_at = datetime.now()
        
        recent_files = context.active_files[-3:] if context.active_files else ["Unknown files"]
        context.summary = f"Parked on {context.parked_at.strftime('%Y-%m-%d %H:%M')}. Was working on {', '.join(recent_files)}."
        
        self._save_contexts()
        self.current_project = None
        
        return context

    def get_active_projects(self, hours: int = 72) -> List[ProjectContext]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [ctx for ctx in self.contexts.values() if ctx.last_active >= cutoff]

    def get_current_project(self) -> Optional[str]:
        entry = context_watcher.get_current_context()
        if entry:
            detected = self.detect_project_switch(entry.app_name, entry.window_title)
            if detected:
                return detected
        return self.current_project

context_switcher = ContextSwitcher()
