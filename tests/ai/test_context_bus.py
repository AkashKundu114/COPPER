import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.ai.orchestration.context_bus import ContextBus, InterAgentMessage


@pytest.mark.asyncio
async def test_context_bus_set_and_get():
    bus = ContextBus()
    dag_id = "test_dag_101"

    await bus.set_context(dag_id, "csv_rows", 1500)
    await bus.set_context(dag_id, "report_format", "PDF")

    assert await bus.get_context(dag_id, "csv_rows") == 1500
    assert await bus.get_context(dag_id, "report_format") == "PDF"
    assert await bus.get_context(dag_id, "non_existent", "default_val") == "default_val"

    all_ctx = await bus.get_all_context(dag_id)
    assert all_ctx["csv_rows"] == 1500
    assert all_ctx["report_format"] == "PDF"


@pytest.mark.asyncio
async def test_context_bus_inter_agent_messaging():
    bus = ContextBus()
    dag_id = "test_dag_102"

    msg1 = await bus.send_message(
        dag_id=dag_id,
        sender="OMNI",
        recipient="AXIS",
        message_type="data_transfer",
        content="Passing extracted CSV metrics: Q1 revenue +24%",
        payload={"metrics": {"growth": 0.24}},
    )

    assert msg1.sender == "OMNI"
    assert msg1.recipient == "AXIS"
    assert "24%" in msg1.content

    msg2 = await bus.send_message(
        dag_id=dag_id,
        sender="AXIS",
        recipient="FORGE",
        message_type="task_handoff",
        content="Generated visualization script plot_trends.py",
        payload={"script": "import matplotlib..."},
    )

    messages = bus.get_messages(dag_id)
    assert len(messages) == 2
    assert messages[0]["sender"] == "OMNI"
    assert messages[1]["recipient"] == "FORGE"


@pytest.mark.asyncio
async def test_context_bus_subscriptions_and_events():
    bus = ContextBus()
    dag_id = "test_dag_103"
    received_events = []

    async def listener(event):
        received_events.append(event)

    bus.subscribe(dag_id, listener)

    await bus.publish_event(
        session_id=None,
        dag_id=dag_id,
        event_type="task_graph_step_start",
        payload={"id": "T1", "agent": "OMNI", "title": "Analyze Data"},
    )

    assert len(received_events) == 1
    assert received_events[0]["type"] == "task_graph_step_start"
    assert received_events[0]["id"] == "T1"

    bus.unsubscribe(dag_id, listener)
    await bus.publish_event(session_id=None, dag_id=dag_id, event_type="task_graph_complete", payload={})
    # Should not receive after unsubscribe
    assert len(received_events) == 1


@pytest.mark.asyncio
async def test_context_bus_trace_history():
    bus = ContextBus()
    dag_id = "test_dag_104"

    trace_data = {
        "dag_id": dag_id,
        "goal": "Test trace storage",
        "success": True,
        "total_duration_ms": 120.5,
    }

    bus.record_trace(dag_id, trace_data)
    retrieved = bus.get_trace(dag_id)
    assert retrieved is not None
    assert retrieved["goal"] == "Test trace storage"

    traces = bus.list_traces(limit=10)
    assert len(traces) >= 1
    assert traces[0]["dag_id"] == dag_id
