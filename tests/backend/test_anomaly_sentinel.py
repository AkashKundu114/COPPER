import time
from app.core.anomaly_sentinel import AnomalySentinel, AnomalyAlert
from app.core.constants import AlertSeverity

def test_no_alerts_on_clean_state():
    s = AnomalySentinel()
    s.record_interaction()
    alerts = s.run_checks()
    assert len(alerts) == 0

def test_rabbit_hole_detection():
    s = AnomalySentinel()
    s.record_interaction()
    for _ in range(4):
        s.record_error('docker build', 'exit code 1')
    alerts = s.run_checks()
    rabbit = [a for a in alerts if a.category == 'rabbit_hole']
    assert len(rabbit) == 1
    assert rabbit[0].severity == AlertSeverity.WARNING

def test_stuck_task_detection():
    s = AnomalySentinel()
    s.record_interaction()
    s._task_start_times['debug_query'] = time.time() - 2800
    alerts = s.run_checks()
    stuck = [a for a in alerts if a.category == 'stuck_task']
    assert len(stuck) == 1
    assert '46' in stuck[0].message or '47' in stuck[0].message or 'minutes' in stuck[0].message

def test_alert_dismiss():
    s = AnomalySentinel()
    s.record_interaction()
    for _ in range(4):
        s.record_error('docker build', 'exit code 1')
    alerts = s.run_checks()
    assert len([a for a in alerts if a.category == 'rabbit_hole']) == 1
    s.dismiss_alert('rabbit_hole_repeat')
    alerts2 = s.run_checks()
    assert len([a for a in alerts2 if a.category == 'rabbit_hole']) == 0

def test_alert_to_dict():
    alert = AnomalyAlert(alert_id='test', severity=AlertSeverity.INFO, category='test', title='Test', message='Test message')
    d = alert.to_dict()
    assert d['alert_id'] == 'test'
    assert d['severity'] == 'info'
    assert d['mode'] == 'normal'

def test_context_thrashing_detection():
    s = AnomalySentinel()
    s.record_interaction()
    for _ in range(6):
        s.record_context_switch()
        time.sleep(0.01)
    # Clear the rate limiter to ensure the alert gets through immediately
    s._last_alert_time = 0
    alerts = s.run_checks()
    thrashing = [a for a in alerts if a.category == 'focus']
    assert len(thrashing) == 1
    assert thrashing[0].severity == AlertSeverity.WARNING
