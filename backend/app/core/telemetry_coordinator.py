"""Unified Telemetry & Correlation Coordinator for C.O.P.P.E.R.

Provides distributed tracing context, span lifecycle management, metrics correlation,
and structured diagnostic traces across inference and agent execution chains.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from app.core.logger import logger
from app.core.metrics import metrics_registry


@dataclass
class TelemetrySpan:
    trace_id: str
    span_id: str
    name: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    error_message: str | None = None

    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000.0
        return (self.end_time - self.start_time) * 1000.0

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def finish(self, status: str = "OK", error: str | None = None) -> None:
        self.end_time = time.time()
        self.status = status
        self.error_message = error


class TelemetryCoordinator:
    """Manages distributed trace correlation, span hierarchy, and operational metrics."""

    def __init__(self, metrics=None):
        self.metrics = metrics or metrics_registry
        self._active_spans: dict[str, TelemetrySpan] = {}
        self._completed_spans: list[TelemetrySpan] = []

    def create_trace_id(self) -> str:
        return uuid.uuid4().hex

    def create_span_id(self) -> str:
        return uuid.uuid4().hex[:16]

    @asynccontextmanager
    async def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncGenerator[TelemetrySpan, None]:
        tid = trace_id or self.create_trace_id()
        sid = self.create_span_id()
        span = TelemetrySpan(
            trace_id=tid,
            span_id=sid,
            name=name,
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        self._active_spans[sid] = span
        logger.debug(f"[TelemetryCoordinator] Started span '{name}' [trace={tid[:8]}, span={sid}]")

        try:
            yield span
            span.finish(status="OK")
        except Exception as exc:
            span.finish(status="ERROR", error=str(exc))
            if hasattr(self.metrics, "security_events"):
                self.metrics.security_events.inc(labels={"type": "span_error", "name": name})
            raise
        finally:
            self._active_spans.pop(sid, None)
            self._completed_spans.append(span)
            # Bound completed spans list to prevent memory growth
            if len(self._completed_spans) > 2000:
                self._completed_spans = self._completed_spans[-1000:]
            logger.debug(
                f"[TelemetryCoordinator] Finished span '{name}' [duration={span.duration_ms:.2f}ms, status={span.status}]"
            )

    def get_recent_spans(self, trace_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Returns structured trace summaries for verification and observability dashboards."""
        spans = self._completed_spans
        if trace_id:
            spans = [s for s in spans if s.trace_id == trace_id]
        
        return [
            {
                "trace_id": s.trace_id,
                "span_id": s.span_id,
                "name": s.name,
                "parent_span_id": s.parent_span_id,
                "duration_ms": round(s.duration_ms, 2),
                "status": s.status,
                "attributes": s.attributes,
                "events_count": len(s.events),
                "error": s.error_message,
            }
            for s in spans[-limit:]
        ]


telemetry_coordinator = TelemetryCoordinator()
