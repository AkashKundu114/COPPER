import time
from dataclasses import dataclass, field
from typing import Optional
from app.core.constants import AlertSeverity, AlertMode
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
        return {'alert_id': self.alert_id, 'severity': self.severity.value, 'category': self.category, 'title': self.title, 'message': self.message, 'mode': self.mode.value, 'suggested_actions': self.suggested_actions}

class AnomalySentinel:

    def __init__(self):
        self._error_log: list[dict] = []
        self._task_start_times: dict[str, float] = {}
        self._last_interaction_time: float = time.time()
        self._suppressed: set[str] = set()

    def record_error(self, context: str, error: str) -> None:
        self._error_log.append({'context': context, 'error': error, 'time': time.time()})
        self._error_log = self._error_log[-50:]

    def record_interaction(self) -> None:
        self._last_interaction_time = time.time()

    def record_task_start(self, task_id: str) -> None:
        self._task_start_times[task_id] = time.time()

    def record_task_end(self, task_id: str) -> None:
        self._task_start_times.pop(task_id, None)

    def dismiss_alert(self, alert_id: str) -> None:
        self._suppressed.add(alert_id)

    def run_checks(self) -> list[AnomalyAlert]:
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
        if alerts:
            logger.info(f'[spider-sense] {len(alerts)} anomaly alert(s) triggered')
        return alerts

    def _check_rabbit_hole(self) -> Optional[AnomalyAlert]:
        now = time.time()
        recent_errors = [e for e in self._error_log if now - e['time'] < 300]
        if len(recent_errors) >= 3:
            contexts = [e['context'] for e in recent_errors[-3:]]
            if len(set(contexts)) == 1:
                return AnomalyAlert(alert_id='rabbit_hole_repeat', severity=AlertSeverity.WARNING, category='rabbit_hole', title='Repeated Failure Detected', message=f'You have hit {len(recent_errors)} errors in the last 5 minutes on "{contexts[0]}". You may be repeating the same approach — consider stepping back.', mode=AlertMode.FOCUSED, suggested_actions=['Step back and rethink', 'Ask C.O.P.P.E.R. for help', 'Snooze 15m'])
        return None

    def _check_stuck_tasks(self) -> Optional[AnomalyAlert]:
        now = time.time()
        for task_id, start in self._task_start_times.items():
            elapsed_min = (now - start) / 60
            if elapsed_min > 45:
                return AnomalyAlert(alert_id=f'stuck_task_{task_id}', severity=AlertSeverity.WARNING, category='stuck_task', title='Extended Task Duration', message=f'You have been working on "{task_id}" for {int(elapsed_min)} minutes. Consider taking a break or switching approach.', mode=AlertMode.FOCUSED, suggested_actions=['Take a break', 'Switch approach', 'Snooze 30m'])
        return None

    def _check_idle_session(self) -> Optional[AnomalyAlert]:
        now = time.time()
        idle_min = (now - self._last_interaction_time) / 60
        hour = time.localtime().tm_hour
        if 8 <= hour <= 22 and idle_min > 30:
            return AnomalyAlert(alert_id='idle_session', severity=AlertSeverity.INFO, category='idle', title='Session Idle', message=f'No interaction for {int(idle_min)} minutes. Everything okay?', mode=AlertMode.NORMAL, suggested_actions=['I\'m here', 'Snooze 1h'])
        return None

sentinel = AnomalySentinel()
