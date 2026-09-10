import contextlib
import time
from collections import OrderedDict
from typing import Any

from fastapi import FastAPI
from opentelemetry import context, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHttpSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from app.core.config import settings
from app.core.logger import logger


class LiveSpanCollector(SpanProcessor):
    """
    In-memory ring buffer collector that stores completed root traces and their
    hierarchical child spans (WebSocket -> Router -> Guardian -> Agent -> LLM -> Response).
    Allows the frontend Activity View to render real-time span waterfalls with zero
    external dependency on Tempo or network latency.
    """

    def __init__(self, max_traces: int = 200):
        self.max_traces = max_traces
        # Maps trace_id_hex -> list of raw span records
        self._traces: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()

    def on_start(self, span: Span, parent_context=None) -> None:
        pass

    def on_end(self, span: ReadableSpan) -> None:
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return

        trace_id_hex = f"{ctx.trace_id:032x}"
        span_id_hex = f"{ctx.span_id:016x}"
        parent_id_hex = f"{span.parent.span_id:016x}" if span.parent else None

        # Convert nanoseconds to milliseconds
        start_ms = span.start_time / 1e6
        end_ms = (span.end_time or time.time_ns()) / 1e6
        duration_ms = max(0.01, round(end_ms - start_ms, 2))

        # Format attributes safely
        clean_attrs = {}
        for k, v in (span.attributes or {}).items():
            if isinstance(v, (str, int, float, bool)):
                clean_attrs[k] = v
            else:
                clean_attrs[k] = str(v)

        span_record = {
            "span_id": span_id_hex,
            "name": span.name,
            "parent_id": parent_id_hex,
            "start_time_ms": round(start_ms, 2),
            "end_time_ms": round(end_ms, 2),
            "duration_ms": duration_ms,
            "status": span.status.status_code.name if span.status else "UNSET",
            "attributes": clean_attrs,
        }

        if trace_id_hex not in self._traces:
            self._traces[trace_id_hex] = []
            if len(self._traces) > self.max_traces:
                self._traces.popitem(last=False)

        self._traces[trace_id_hex].append(span_record)

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def get_traces(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return formatted traces ordered from newest to oldest."""
        result = []
        for trace_id, spans in reversed(list(self._traces.items())[-limit:]):
            if not spans:
                continue

            # Identify root span (either no parent, or first registered span)
            root_span = next((s for s in spans if s["parent_id"] is None), spans[0])
            overall_start = min(s["start_time_ms"] for s in spans)
            overall_end = max(s["end_time_ms"] for s in spans)
            total_duration_ms = round(overall_end - overall_start, 2)

            # Compute relative offsets for waterfall rendering
            formatted_spans = []
            for s in spans:
                offset_ms = round(max(0.0, s["start_time_ms"] - overall_start), 2)
                formatted_spans.append({
                    **s,
                    "offset_ms": offset_ms,
                })

            result.append({
                "trace_id": trace_id,
                "root_name": root_span["name"],
                "timestamp": root_span["start_time_ms"],
                "duration_ms": total_duration_ms,
                "status": "error" if any(s["status"] == "ERROR" for s in spans) else "success",
                "spans_count": len(spans),
                "spans": formatted_spans,
                "root_attributes": root_span.get("attributes", {}),
                "grafana_url": format_grafana_tempo_url(trace_id),
            })
        return result

    def get_trace_by_id(self, trace_id: str) -> dict[str, Any] | None:
        spans = self._traces.get(trace_id)
        if not spans:
            return None

        root_span = next((s for s in spans if s["parent_id"] is None), spans[0])
        overall_start = min(s["start_time_ms"] for s in spans)
        overall_end = max(s["end_time_ms"] for s in spans)
        total_duration_ms = round(overall_end - overall_start, 2)

        formatted_spans = []
        for s in spans:
            offset_ms = round(max(0.0, s["start_time_ms"] - overall_start), 2)
            formatted_spans.append({
                **s,
                "offset_ms": offset_ms,
            })

        return {
            "trace_id": trace_id,
            "root_name": root_span["name"],
            "timestamp": root_span["start_time_ms"],
            "duration_ms": total_duration_ms,
            "status": "error" if any(s["status"] == "ERROR" for s in spans) else "success",
            "spans_count": len(spans),
            "spans": formatted_spans,
            "root_attributes": root_span.get("attributes", {}),
            "grafana_url": format_grafana_tempo_url(trace_id),
        }


# Global singleton instances
live_span_collector = LiveSpanCollector()
_tracer_provider: TracerProvider | None = None
_is_initialized: bool = False
propagator = TraceContextTextMapPropagator()


def format_grafana_tempo_url(trace_id: str) -> str:
    """Formats a deep-link URL into Grafana Explore targeting Tempo."""
    base = settings.GRAFANA_URL.rstrip("/")
    import json
    import urllib.parse

    explore_query = [{"datasource": "Tempo", "queries": [{"query": trace_id}]}]
    encoded = urllib.parse.quote(json.dumps(explore_query))
    return f"{base}/explore?left={encoded}"


def init_telemetry(app: FastAPI | None = None) -> TracerProvider:
    """
    Initializes OpenTelemetry TracerProvider, OTLP Exporter targeting Grafana Tempo,
    in-memory live span collector, and instruments FastAPI if app is supplied.
    """
    global _tracer_provider, _is_initialized

    if _is_initialized and _tracer_provider is not None:
        return _tracer_provider

    resource = Resource.create(
        {
            SERVICE_NAME: settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": getattr(settings, "APP_ENV", "development"),
        }
    )

    provider = TracerProvider(resource=resource)

    # 1. Attach live in-memory span collector (guarantees frontend Activity View always works)
    provider.add_span_processor(live_span_collector)

    # 2. Attach OTLP Exporter targeting Tempo if enabled
    if settings.OTEL_ENABLED:
        try:
            endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
            # Default to gRPC exporter
            otlp_exporter = OTLPGrpcSpanExporter(
                endpoint=endpoint,
                insecure=True,
                timeout=2,
            )
            provider.add_span_processor(
                BatchSpanProcessor(
                    otlp_exporter,
                    max_queue_size=2048,
                    schedule_delay_millis=500,
                    export_timeout_millis=2000,
                )
            )
            logger.info(f"OpenTelemetry OTLP Exporter configured for Tempo at {endpoint}")
        except Exception as e:
            logger.warning(f"Could not initialize OTLP gRPC exporter: {e}. Falling back to live collector.")

    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    _is_initialized = True

    # 3. Instrument FastAPI app if provided
    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=provider,
                excluded_urls="health,metrics,docs,openapi.json",
            )
            logger.info("FastAPI OpenTelemetry instrumentation attached successfully")
        except Exception as e:
            logger.warning(f"FastAPI instrumentor warning: {e}")

    return provider


def get_tracer(name: str = "copper") -> trace.Tracer:
    """Returns an OpenTelemetry tracer."""
    return trace.get_tracer(name, settings.APP_VERSION)


@contextlib.contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None, parent_context=None):
    """
    Synchronous / asynchronous context manager for tracing execution stages.
    Records duration, status, attributes, and exceptions.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name, context=parent_context) as span:
        if attributes:
            for k, v in attributes.items():
                if v is not None:
                    span.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else str(v))
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def start_request_trace(
    name: str,
    session_id: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> tuple[trace.Span, str, str]:
    """
    Starts a root trace span for a request/turn and activates it in the current context,
    returning: (span, trace_id_hex, span_id_hex).
    When span.end() is called, context is automatically detached.
    """
    tracer = get_tracer()
    span = tracer.start_span(name)
    ctx = span.get_span_context()
    trace_id_hex = f"{ctx.trace_id:032x}"
    span_id_hex = f"{ctx.span_id:016x}"

    span.set_attribute("copper.session_id", session_id or "")
    span.set_attribute("copper.trace_id", trace_id_hex)
    if attributes:
        for k, v in attributes.items():
            if v is not None:
                span.set_attribute(k, v if isinstance(v, (str, int, float, bool)) else str(v))

    # Activate span in current context so all subsequent child spans automatically nest under it
    token = context.attach(trace.set_span_in_context(span))
    original_end = span.end

    def wrapped_end(*args, **kwargs):
        try:
            context.detach(token)
        except Exception:
            pass
        return original_end(*args, **kwargs)

    span.end = wrapped_end  # type: ignore
    return span, trace_id_hex, span_id_hex


@contextlib.contextmanager
def trace_turn(
    name: str,
    session_id: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """Context manager for tracing an entire turn / request lifecycle."""
    span, trace_id, span_id = start_request_trace(name, session_id=session_id, attributes=attributes)
    try:
        yield span, trace_id, span_id
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        raise
    finally:
        span.end()


def get_recent_traces(limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve recent distributed traces from the live collector."""
    return live_span_collector.get_traces(limit=limit)


def get_trace_by_id(trace_id: str) -> dict[str, Any] | None:
    """Retrieve a single distributed trace with all spans."""
    return live_span_collector.get_trace_by_id(trace_id)
