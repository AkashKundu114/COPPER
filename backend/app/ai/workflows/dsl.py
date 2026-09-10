import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logger import logger


class TriggerType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    EVENT = "event"
    MANUAL = "manual"


class ActionFailurePolicy(str, Enum):
    SKIP = "skip"
    RETRY = "retry"
    ABORT = "abort"


@dataclass
class TriggerConfig:
    type: TriggerType | str
    value: str | dict[str, Any] = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value if isinstance(self.type, TriggerType) else str(self.type),
            "value": self.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TriggerConfig":
        raw_type = data.get("type", "manual")
        try:
            t_type = TriggerType(raw_type)
        except ValueError:
            t_type = raw_type
        return cls(
            type=t_type,
            value=data.get("value", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Condition:
    field: str
    operator: str  # "==", "!=", ">", "<", ">=", "<=", "contains", "in"
    value: Any

    def evaluate(self, context: dict[str, Any]) -> bool:
        val = context.get(self.field)
        op = self.operator
        try:
            if op in ("==", "eq"):
                return val == self.value
            elif op in ("!=", "neq"):
                return val != self.value
            elif op in (">", "gt"):
                return val is not None and float(val) > float(self.value)
            elif op in ("<", "lt"):
                return val is not None and float(val) < float(self.value)
            elif op in (">=", "gte"):
                return val is not None and float(val) >= float(self.value)
            elif op in ("<=", "lte"):
                return val is not None and float(val) <= float(self.value)
            elif op == "contains":
                return self.value in val if val is not None else False
            elif op == "in":
                return val in self.value if self.value is not None else False
            return False
        except Exception as e:
            logger.warning(f"Condition evaluation error ({self.field} {self.operator} {self.value}): {e}")
            return False

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Condition":
        return cls(
            field=data.get("field", ""),
            operator=data.get("operator", "=="),
            value=data.get("value"),
        )


@dataclass
class WorkflowAction:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    on_failure: ActionFailurePolicy | str = ActionFailurePolicy.SKIP
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": self.arguments,
            "on_failure": self.on_failure.value if isinstance(self.on_failure, ActionFailurePolicy) else str(self.on_failure),
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowAction":
        raw_policy = data.get("on_failure", "skip")
        try:
            policy = ActionFailurePolicy(raw_policy)
        except ValueError:
            policy = ActionFailurePolicy.SKIP
        return cls(
            tool=data.get("tool", ""),
            arguments=data.get("arguments", {}),
            on_failure=policy,
            max_retries=int(data.get("max_retries", 3)),
            retry_delay_seconds=float(data.get("retry_delay_seconds", 1.0)),
        )


@dataclass
class NotificationConfig:
    type: str = "toast"  # "toast", "websocket", "silent"
    template: str = "Workflow '{name}' executed with status: {status}"
    channels: list[str] = field(default_factory=lambda: ["websocket"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "template": self.template,
            "channels": self.channels,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationConfig":
        return cls(
            type=data.get("type", "toast"),
            template=data.get("template", "Workflow '{name}' executed with status: {status}"),
            channels=data.get("channels", ["websocket"]),
        )


@dataclass
class Workflow:
    name: str
    description: str = ""
    trigger: TriggerConfig = field(default_factory=lambda: TriggerConfig(type=TriggerType.MANUAL))
    conditions: list[Condition] = field(default_factory=list)
    actions: list[WorkflowAction] = field(default_factory=list)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    enabled: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_run: float | None = None
    last_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.to_dict(),
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "notification": self.notification.to_dict(),
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_run": self.last_run,
            "last_status": self.last_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        trigger_raw = data.get("trigger", {})
        trigger = TriggerConfig.from_dict(trigger_raw) if isinstance(trigger_raw, dict) else TriggerConfig(type=TriggerType.MANUAL)

        conditions = [
            Condition.from_dict(c) if isinstance(c, dict) else c
            for c in data.get("conditions", [])
        ]
        actions = [
            WorkflowAction.from_dict(a) if isinstance(a, dict) else a
            for a in data.get("actions", [])
        ]
        notif_raw = data.get("notification", {})
        notification = NotificationConfig.from_dict(notif_raw) if isinstance(notif_raw, dict) else NotificationConfig()

        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            name=data.get("name", "Untitled Workflow"),
            description=data.get("description", ""),
            trigger=trigger,
            conditions=conditions,
            actions=actions,
            notification=notification,
            enabled=bool(data.get("enabled", True)),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            last_run=data.get("last_run"),
            last_status=data.get("last_status"),
        )


@dataclass
class ExecutionRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    started_at: float = field(default_factory=time.time)
    completed_at: float = field(default_factory=time.time)
    status: str = "success"  # "success", "failed", "partial", "aborted", "skipped"
    action_results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    notification_sent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "action_results": self.action_results,
            "error": self.error,
            "notification_sent": self.notification_sent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionRecord":
        return cls(
            id=data.get("id") or str(uuid.uuid4()),
            workflow_id=data.get("workflow_id", ""),
            workflow_name=data.get("workflow_name", ""),
            started_at=float(data.get("started_at", time.time())),
            completed_at=float(data.get("completed_at", time.time())),
            status=data.get("status", "success"),
            action_results=data.get("action_results", []),
            error=data.get("error"),
            notification_sent=bool(data.get("notification_sent", False)),
        )


class WorkflowStore:
    def __init__(self, storage_path: str | Path | None = None, history_path: str | Path | None = None):
        if storage_path is not None:
            self.storage_path = Path(storage_path)
        else:
            base_dir = Path(settings.DB_PATH).parent if hasattr(settings, "DB_PATH") else Path("data")
            self.storage_path = base_dir / "workflows.json"

        if history_path is not None:
            self.history_path = Path(history_path)
        else:
            self.history_path = self.storage_path.parent / "workflow_history.json"

        self._workflows: dict[str, Workflow] = {}
        self._history: list[ExecutionRecord] = []
        self._ensure_storage_exists()
        self.load()

    def _ensure_storage_exists(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create workflows directory: {e}")

    def load(self):
        # Load workflows
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._workflows = {item["id"]: Workflow.from_dict(item) for item in data if "id" in item}
                    elif isinstance(data, dict):
                        self._workflows = {k: Workflow.from_dict(v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._workflows)} workflows from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load workflows from {self.storage_path}: {e}")
                self._workflows = {}
        else:
            self._workflows = {}

        # Load history
        if self.history_path.exists():
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    hist_data = json.load(f)
                    if isinstance(hist_data, list):
                        self._history = [ExecutionRecord.from_dict(item) for item in hist_data]
            except Exception as e:
                logger.error(f"Failed to load workflow history from {self.history_path}: {e}")
                self._history = []
        else:
            self._history = []

    def save(self):
        self._ensure_storage_exists()
        try:
            temp_file = self.storage_path.with_suffix(".tmp")
            data = [w.to_dict() for w in self._workflows.values()]
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.storage_path)
        except Exception as e:
            logger.error(f"Failed to persist workflows to {self.storage_path}: {e}")

    def save_history(self):
        self._ensure_storage_exists()
        try:
            temp_file = self.history_path.with_suffix(".tmp")
            data = [h.to_dict() for h in self._history[-1000:]]  # Cap history to last 1000 runs
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.history_path)
        except Exception as e:
            logger.error(f"Failed to persist workflow history to {self.history_path}: {e}")

    def get_all(self, enabled_only: bool = False) -> list[Workflow]:
        workflows = list(self._workflows.values())
        if enabled_only:
            return [w for w in workflows if w.enabled]
        return workflows

    def get(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def create(self, workflow: Workflow) -> Workflow:
        if not workflow.id:
            workflow.id = str(uuid.uuid4())
        workflow.created_at = time.time()
        workflow.updated_at = time.time()
        self._workflows[workflow.id] = workflow
        self.save()
        logger.info(f"Created workflow '{workflow.name}' ({workflow.id})")
        return workflow

    def update(self, workflow: Workflow) -> Workflow | None:
        if workflow.id not in self._workflows:
            return None
        workflow.updated_at = time.time()
        self._workflows[workflow.id] = workflow
        self.save()
        logger.info(f"Updated workflow '{workflow.name}' ({workflow.id})")
        return workflow

    def delete(self, workflow_id: str) -> bool:
        if workflow_id in self._workflows:
            removed = self._workflows.pop(workflow_id)
            self.save()
            logger.info(f"Deleted workflow '{removed.name}' ({workflow_id})")
            return True
        return False

    def toggle(self, workflow_id: str, enabled: bool | None = None) -> Workflow | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        if enabled is None:
            wf.enabled = not wf.enabled
        else:
            wf.enabled = bool(enabled)
        wf.updated_at = time.time()
        self.save()
        logger.info(f"Toggled workflow '{wf.name}' ({workflow_id}) enabled={wf.enabled}")
        return wf

    def add_history(self, record: ExecutionRecord) -> None:
        self._history.append(record)
        if len(self._history) > 1000:
            self._history = self._history[-1000:]
        self.save_history()

    def get_history(self, workflow_id: str, limit: int = 50) -> list[ExecutionRecord]:
        matching = [r for r in self._history if r.workflow_id == workflow_id]
        matching.sort(key=lambda r: r.started_at, reverse=True)
        return matching[:limit]


workflow_store = WorkflowStore()
