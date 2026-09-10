import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.testclient import TestClient

from app.ai.tools.executor import ToolResult, tool_executor
from app.ai.workflows.dsl import (
    ActionFailurePolicy,
    Condition,
    ExecutionRecord,
    NotificationConfig,
    TriggerConfig,
    TriggerType,
    Workflow,
    WorkflowAction,
    WorkflowStore,
)
from app.ai.workflows.trigger_parser import (
    TriggerParser,
    parse_interval_seconds,
    validate_cron_expression,
)
from app.ai.workflows.workflow_engine import WorkflowEngine
from app.main import app


@pytest.fixture
def temp_store():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = Path(tmp_dir) / "workflows.json"
        history_path = Path(tmp_dir) / "workflow_history.json"
        store = WorkflowStore(storage_path=storage_path, history_path=history_path)
        yield store


def test_workflow_dsl_and_store_crud(temp_store):
    # 1. Create workflow
    wf = Workflow(
        name="Test Morning Automation",
        description="A test workflow",
        trigger=TriggerConfig(type=TriggerType.CRON, value="0 9 * * *"),
        conditions=[Condition(field="battery", operator=">", value=20)],
        actions=[
            WorkflowAction(
                tool="memory_query",
                arguments={"query": "test query"},
                on_failure=ActionFailurePolicy.SKIP,
            )
        ],
        notification=NotificationConfig(type="toast", template="Test completed"),
        enabled=True,
    )

    created = temp_store.create(wf)
    assert created.id is not None
    assert len(temp_store.get_all()) == 1

    # 2. Get workflow
    fetched = temp_store.get(created.id)
    assert fetched is not None
    assert fetched.name == "Test Morning Automation"
    assert fetched.trigger.type == TriggerType.CRON
    assert fetched.trigger.value == "0 9 * * *"

    # 3. Update workflow
    fetched.name = "Updated Morning Automation"
    temp_store.update(fetched)
    updated = temp_store.get(created.id)
    assert updated.name == "Updated Morning Automation"

    # 4. Toggle workflow
    toggled = temp_store.toggle(created.id, False)
    assert toggled.enabled is False
    assert len(temp_store.get_all(enabled_only=True)) == 0

    temp_store.toggle(created.id, True)
    assert len(temp_store.get_all(enabled_only=True)) == 1

    # 5. History tracking
    rec = ExecutionRecord(
        workflow_id=created.id,
        workflow_name=created.name,
        status="success",
        action_results=[{"tool": "memory_query", "output": "found 2 items"}],
    )
    temp_store.add_history(rec)
    history = temp_store.get_history(created.id)
    assert len(history) == 1
    assert history[0].workflow_id == created.id
    assert history[0].status == "success"

    # 6. Delete workflow
    deleted = temp_store.delete(created.id)
    assert deleted is True
    assert temp_store.get(created.id) is None
    assert len(temp_store.get_all()) == 0


def test_condition_evaluation():
    cond_eq = Condition(field="status", operator="==", value="active")
    assert cond_eq.evaluate({"status": "active"}) is True
    assert cond_eq.evaluate({"status": "inactive"}) is False

    cond_gt = Condition(field="cpu_usage", operator=">", value=80)
    assert cond_gt.evaluate({"cpu_usage": 85}) is True
    assert cond_gt.evaluate({"cpu_usage": 75}) is False

    cond_contains = Condition(field="message", operator="contains", value="alert")
    assert cond_contains.evaluate({"message": "critical alert triggered"}) is True
    assert cond_contains.evaluate({"message": "normal operation"}) is False


def test_cron_and_interval_validators():
    # Valid cron
    ok, err = validate_cron_expression("0 9 * * *")
    assert ok is True
    assert err is None

    ok, err = validate_cron_expression("0 9 * * MON-FRI")
    assert ok is True
    assert err is None

    # Invalid cron
    ok, err = validate_cron_expression("not a cron")
    assert ok is False
    assert err is not None

    # Interval parsing
    ok, secs, err = parse_interval_seconds("30s")
    assert ok and secs == 30.0

    ok, secs, err = parse_interval_seconds("15m")
    assert ok and secs == 900.0

    ok, secs, err = parse_interval_seconds("2h")
    assert ok and secs == 7200.0

    ok, secs, err = parse_interval_seconds(60)
    assert ok and secs == 60.0

    ok, secs, err = parse_interval_seconds("-5s")
    assert not ok


@pytest.mark.asyncio
async def test_trigger_parser_heuristics():
    parser = TriggerParser()

    # Prompt 1: Morning task summary
    res1 = await parser.parse("Every morning at 9am, summarize my overdue tasks")
    assert res1.success is True
    assert res1.workflow is not None
    assert res1.workflow.trigger.type == TriggerType.CRON
    assert res1.workflow.trigger.value == "0 9 * * *"
    assert len(res1.workflow.actions) >= 1
    assert res1.workflow.actions[0].tool == "memory_query"

    # Prompt 2: Weekday morning
    res2 = await parser.parse("Weekday mornings at 9am, summarize my overdue tasks")
    assert res2.success is True
    assert res2.workflow.trigger.value == "0 9 * * MON-FRI"

    # Prompt 3: App launch event
    res3 = await parser.parse("When I open VS Code, load my project context")
    assert res3.success is True
    assert res3.workflow.trigger.type == TriggerType.EVENT
    assert res3.workflow.trigger.value == "on_app_launch"
    assert res3.workflow.trigger.metadata.get("app") == "Code.exe"

    # Prompt 4: Interval periodic
    res4 = await parser.parse("Every 15 minutes, check system status")
    assert res4.success is True
    assert res4.workflow.trigger.type == TriggerType.INTERVAL
    assert res4.workflow.trigger.value == "15m"

    # Prompt 5: Ambiguous prompt returns clarification questions
    res5 = await parser.parse("Sometime later, do something with my files")
    assert res5.success is False
    assert len(res5.questions) > 0


def test_trigger_parser_tool_validation():
    parser = TriggerParser()

    # Valid data
    valid_data = {
        "name": "File backup",
        "description": "Read and backup",
        "trigger": {"type": "cron", "value": "0 0 * * *"},
        "actions": [{"tool": "file_read", "arguments": {"path": "test.txt"}, "on_failure": "skip"}],
        "enabled": True,
    }
    res_valid = parser.validate_workflow_data(valid_data)
    assert res_valid.success is True

    # Invalid tool name
    invalid_data = {
        "name": "Send email",
        "trigger": {"type": "cron", "value": "0 0 * * *"},
        "actions": [{"tool": "unsupported_magic_tool", "arguments": {}}],
    }
    res_invalid = parser.validate_workflow_data(invalid_data)
    assert res_invalid.success is False
    assert any("unsupported_magic_tool" in q for q in res_invalid.questions)


@pytest.mark.asyncio
async def test_workflow_engine_execution(temp_store):
    engine = WorkflowEngine(store=temp_store)

    wf = Workflow(
        name="Sequential Workflow",
        trigger=TriggerConfig(type=TriggerType.MANUAL),
        actions=[
            WorkflowAction(tool="memory_query", arguments={"query": "test context"}),
            WorkflowAction(tool="shell_execute", arguments={"command": "echo done"}),
        ],
        notification=NotificationConfig(type="toast", template="Workflow '{name}' finished with status: {status}"),
        enabled=True,
    )
    temp_store.create(wf)

    mock_result1 = ToolResult(
        tool_name="memory_query",
        arguments={"query": "test context"},
        output={"results": ["Task 1", "Task 2"]},
        success=True,
        execution_time_ms=12.0,
    )
    mock_result2 = ToolResult(
        tool_name="shell_execute",
        arguments={"command": "echo done"},
        output="done",
        success=True,
        execution_time_ms=5.0,
    )

    with patch.object(tool_executor, "execute", side_effect=[mock_result1, mock_result2]):
        with patch("app.api.websocket.manager.manager.push_proactive", new_callable=AsyncMock) as mock_push:
            with patch("app.api.websocket.manager.manager.broadcast", new_callable=AsyncMock) as mock_broadcast:
                record = await engine.execute_workflow(wf.id)

                assert record.status == "success"
                assert len(record.action_results) == 2
                assert record.action_results[0]["success"] is True
                assert record.action_results[1]["output"] == "done"
                assert mock_push.called
                assert mock_broadcast.called

    # Verify history was saved
    history = temp_store.get_history(wf.id)
    assert len(history) == 1
    assert history[0].status == "success"


@pytest.mark.asyncio
async def test_workflow_engine_failure_policies(temp_store):
    engine = WorkflowEngine(store=temp_store)

    # 1. Test ABORT policy: step 1 fails, step 2 should NOT execute
    wf_abort = Workflow(
        name="Abort On Failure Workflow",
        trigger=TriggerConfig(type=TriggerType.MANUAL),
        actions=[
            WorkflowAction(tool="shell_execute", arguments={"command": "fail"}, on_failure=ActionFailurePolicy.ABORT),
            WorkflowAction(tool="memory_query", arguments={"query": "should not run"}),
        ],
        enabled=True,
    )
    temp_store.create(wf_abort)

    fail_res = ToolResult(
        tool_name="shell_execute",
        arguments={"command": "fail"},
        output=None,
        success=False,
        error="Command failed with code 1",
    )

    with patch.object(tool_executor, "execute", return_value=fail_res) as mock_exec:
        record = await engine.execute_workflow(wf_abort.id)
        assert record.status == "aborted"
        assert len(record.action_results) == 1
        assert mock_exec.call_count == 1

    # 2. Test SKIP policy: step 1 fails, step 2 SHOULD execute
    wf_skip = Workflow(
        name="Skip On Failure Workflow",
        trigger=TriggerConfig(type=TriggerType.MANUAL),
        actions=[
            WorkflowAction(tool="shell_execute", arguments={"command": "fail"}, on_failure=ActionFailurePolicy.SKIP),
            WorkflowAction(tool="memory_query", arguments={"query": "should run"}, on_failure=ActionFailurePolicy.SKIP),
        ],
        enabled=True,
    )
    temp_store.create(wf_skip)

    ok_res = ToolResult(
        tool_name="memory_query",
        arguments={"query": "should run"},
        output="data",
        success=True,
    )

    with patch.object(tool_executor, "execute", side_effect=[fail_res, ok_res]) as mock_exec:
        record = await engine.execute_workflow(wf_skip.id)
        assert record.status == "partial"
        assert len(record.action_results) == 2
        assert mock_exec.call_count == 2

    # 3. Test RETRY policy: action fails initially then succeeds on retry
    wf_retry = Workflow(
        name="Retry On Failure Workflow",
        trigger=TriggerConfig(type=TriggerType.MANUAL),
        actions=[
            WorkflowAction(
                tool="shell_execute",
                arguments={"command": "flaky"},
                on_failure=ActionFailurePolicy.RETRY,
                max_retries=2,
                retry_delay_seconds=0.01,
            )
        ],
        enabled=True,
    )
    temp_store.create(wf_retry)

    with patch.object(tool_executor, "execute", side_effect=[fail_res, ok_res]) as mock_exec:
        record = await engine.execute_workflow(wf_retry.id)
        assert record.status == "success"
        assert mock_exec.call_count == 2


@pytest.mark.asyncio
async def test_workflow_engine_scheduler_registration(temp_store):
    scheduler = AsyncIOScheduler()
    engine = WorkflowEngine(store=temp_store)
    engine.set_scheduler(scheduler)

    cron_wf = Workflow(
        name="Cron Job Workflow",
        trigger=TriggerConfig(type=TriggerType.CRON, value="0 9 * * *"),
        actions=[WorkflowAction(tool="memory_query", arguments={"query": "daily task"})],
        enabled=True,
    )
    temp_store.create(cron_wf)

    # Register workflow
    engine.register_workflow(cron_wf)
    job = scheduler.get_job(f"workflow_{cron_wf.id}")
    assert job is not None
    assert job.name == "Cron Job Workflow"

    # Unregister workflow
    engine.unregister_workflow(cron_wf.id)
    assert scheduler.get_job(f"workflow_{cron_wf.id}") is None


@pytest.mark.asyncio
async def test_event_trigger_dispatcher(temp_store):
    engine = WorkflowEngine(store=temp_store)

    event_wf = Workflow(
        name="On Launch Workflow",
        trigger=TriggerConfig(
            type=TriggerType.EVENT,
            value="on_app_launch",
            metadata={"app": "Code.exe"},
        ),
        actions=[WorkflowAction(tool="memory_query", arguments={"query": "context"})],
        enabled=True,
    )
    temp_store.create(event_wf)
    engine.register_workflow(event_wf)

    with patch.object(
        tool_executor,
        "execute",
        return_value=ToolResult(tool_name="memory_query", arguments={}, output="context", success=True),
    ):
        # Mismatched app event - should not trigger
        records = await engine.trigger_event("on_app_launch", {"app": "notepad.exe"})
        assert len(records) == 0

        # Matching app event - should trigger
        records = await engine.trigger_event("on_app_launch", {"app": "Code.exe"})
        assert len(records) == 1
        assert records[0].status == "success"


def test_api_workflow_routes():
    client = TestClient(app)

    # 1. Create from natural language prompt
    res = client.post(
        "/api/v1/workflows",
        json={"prompt": "Every morning at 9am, summarize my overdue tasks"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    wf_id = data["workflow"]["id"]
    assert wf_id is not None
    assert data["workflow"]["trigger"]["value"] == "0 9 * * *"

    # 2. Ambiguous natural language prompt returns clarification
    ambig_res = client.post(
        "/api/v1/workflows",
        json={"prompt": "someday do some task"},
    )
    assert ambig_res.status_code == 200
    ambig_data = ambig_res.json()
    assert ambig_data.get("status") == "clarification_needed"
    assert len(ambig_data.get("questions", [])) > 0

    # 3. List workflows
    list_res = client.get("/api/v1/workflows")
    assert list_res.status_code == 200
    wf_list = list_res.json()
    assert any(w["id"] == wf_id for w in wf_list)

    # 4. Get single workflow
    get_res = client.get(f"/api/v1/workflows/{wf_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == wf_id

    # 5. Toggle workflow
    toggle_res = client.put(f"/api/v1/workflows/{wf_id}/toggle", json={"enabled": False})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["enabled"] is False

    # 6. Execute manual run
    with patch.object(
        tool_executor,
        "execute",
        return_value=ToolResult(tool_name="memory_query", arguments={}, output="Tasks OK", success=True),
    ):
        run_res = client.post(f"/api/v1/workflows/{wf_id}/run")
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["status"] == "completed"
        assert run_data["record"]["status"] == "success"

    # 7. Get execution history
    hist_res = client.get(f"/api/v1/workflows/{wf_id}/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) >= 1
    assert hist_data[0]["workflow_id"] == wf_id

    # 8. Delete workflow
    del_res = client.delete(f"/api/v1/workflows/{wf_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify 404 after deletion
    get_after_del = client.get(f"/api/v1/workflows/{wf_id}")
    assert get_after_del.status_code == 404
