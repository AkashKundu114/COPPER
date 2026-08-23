import time
from dataclasses import dataclass, field

from app.core.constants import AlertMode, AlertSeverity
from app.core.logger import logger


@dataclass
class AnomalyAlert:
    alert_id: str
    severity: AlertSeverity
    category: str
    title: str
    message: str
    mode: AlertMode = AlertMode.NORMAL
    suggested_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "mode": self.mode.value,
            "suggested_actions": self.suggested_actions,
        }

class AnomalySentinel:
    def __init__(self):
        self._error_log: list[dict] = []
        self._task_start_times: dict[str, float] = {}
        self._last_interaction_time: float = time.time()
        self._suppressed: dict[str, float] = {}
        self._last_alert_time: float = 0.0
        self._context_history: list[float] = []

    def record_error(self, context: str, error: str) -> None:
        self._error_log.append({"context": context, "error": error, "time": time.time()})
        self._error_log = self._error_log[-50:]

    def record_interaction(self) -> None:
        self._last_interaction_time = time.time()

    def record_task_start(self, task_id: str) -> None:
        self._task_start_times[task_id] = time.time()

    def record_task_end(self, task_id: str) -> None:
        self._task_start_times.pop(task_id, None)

    def record_context_switch(self) -> None:
        self._context_history.append(time.time())
        self._context_history = self._context_history[-10:]

    def dismiss_alert(self, alert_id: str) -> None:
        self.snooze_alert(alert_id, 24 * 3600)

    def snooze_alert(self, alert_id: str, duration_seconds: int) -> None:
        self._suppressed[alert_id] = time.time() + duration_seconds
        logger.info(f"[spider-sense] Snoozed alert {alert_id} for {duration_seconds}s")

    def _cleanup(self):
        now = time.time()
        expired = [k for k, v in self._suppressed.items() if v < now]
        for k in expired:
            del self._suppressed[k]
        orphaned = [k for k, v in self._task_start_times.items() if (now - v) > (12 * 3600)]
        for k in orphaned:
            del self._task_start_times[k]

    def run_checks(self) -> list[AnomalyAlert]:
        self._cleanup()
        now = time.time()
        alerts: list[AnomalyAlert] = []

        rabbit_hole = self._check_rabbit_hole()
        if rabbit_hole and rabbit_hole.alert_id not in self._suppressed:
            alerts.append(rabbit_hole)

        stuck_task = self._check_stuck_tasks()
        if stuck_task and stuck_task.alert_id not in self._suppressed:
            alerts.append(stuck_task)

        idle = self._check_idle_session()
        if idle and idle.alert_id not in self._suppressed:
            alerts.append(idle)

        thrashing = self._check_frequent_context_switches()
        if thrashing and thrashing.alert_id not in self._suppressed:
            alerts.append(thrashing)

        schedule = self._check_schedule_drift()
        if schedule and schedule.alert_id not in self._suppressed:
            alerts.append(schedule)

        filtered_alerts = []
        for a in alerts:
            if a.severity == AlertSeverity.CRITICAL or (now - self._last_alert_time) > 60:
                filtered_alerts.append(a)
                if a.severity != AlertSeverity.CRITICAL:
                    self._last_alert_time = now

        if filtered_alerts:
            logger.info(f"[spider-sense] {len(filtered_alerts)} anomaly alert(s) triggered")

        return filtered_alerts

    def _check_rabbit_hole(self) -> AnomalyAlert | None:
        now = time.time()
        recent_errors = [e for e in self._error_log if now - e["time"] < 300]
        if len(recent_errors) >= 3:
            contexts = [e["context"] for e in recent_errors[-3:]]
            if len(set(contexts)) == 1:
                return AnomalyAlert(
                    alert_id="rabbit_hole_repeat",
                    severity=AlertSeverity.WARNING,
                    category="rabbit_hole",
                    title="Repeated Failure Detected",
                    message=f'You have hit {len(recent_errors)} errors in the last 5 minutes on "{contexts[0]}". You may be repeating the same approach — consider stepping back.',
                    mode=AlertMode.FOCUSED,
                    suggested_actions=["Step back and rethink", "Ask C.O.P.P.E.R. for help", "Snooze 15m"],
                )
        return None

    def _check_stuck_tasks(self) -> AnomalyAlert | None:
        now = time.time()
        for task_id, start in self._task_start_times.items():
            elapsed_min = (now - start) / 60
            if 45 < elapsed_min < 12 * 60:
                return AnomalyAlert(
                    alert_id=f"stuck_task_{task_id}",
                    severity=AlertSeverity.WARNING,
                    category="stuck_task",
                    title="Extended Task Duration",
                    message=f'You have been working on "{task_id}" for {int(elapsed_min)} minutes. Consider taking a break or switching approach.',
                    mode=AlertMode.FOCUSED,
                    suggested_actions=["Take a break", "Switch approach", "Snooze 30m"],
                )
        return None

    def _check_idle_session(self) -> AnomalyAlert | None:
        now = time.time()
        idle_min = (now - self._last_interaction_time) / 60
        hour = time.localtime().tm_hour
        if 8 <= hour <= 22 and idle_min > 30:
            return AnomalyAlert(
                alert_id="idle_session",
                severity=AlertSeverity.INFO,
                category="idle",
                title="Session Idle",
                message=f"No interaction for {int(idle_min)} minutes. Everything okay?",
                mode=AlertMode.NORMAL,
                suggested_actions=["I'm here", "Snooze 1h"],
            )
        return None

    def _check_frequent_context_switches(self) -> AnomalyAlert | None:
        now = time.time()
        recent_switches = [t for t in self._context_history if now - t < 600]
        if len(recent_switches) >= 5:
            return AnomalyAlert(
                alert_id="context_thrashing",
                severity=AlertSeverity.WARNING,
                category="focus",
                title="Context Thrashing Detected",
                message="You have switched tasks 5 times in the last 10 minutes. Are you feeling distracted?",
                mode=AlertMode.FOCUSED,
                suggested_actions=["Help me focus", "Snooze 15m"],
            )
        return None

    def _check_schedule_drift(self) -> AnomalyAlert | None:
        now = time.time()
        if not hasattr(self, "_boot_time"):
            self._boot_time = now

        elapsed_since_boot = now - self._boot_time

        if 600 < elapsed_since_boot < 630:
            return AnomalyAlert(
                alert_id="upcoming_meeting_drift",
                severity=AlertSeverity.CRITICAL,
                category="schedule",
                title="Schedule Drift Warning",
                message="You have a 'System Architecture Mock Interview' starting in exactly 5 minutes! Time to wrap up your current task.",
                mode=AlertMode.GUARDIAN,
                suggested_actions=["Save & Close", "I'm ready", "Snooze 2m"],
            )
        return None

sentinel = AnomalySentinel()
