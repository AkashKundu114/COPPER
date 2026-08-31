from unittest.mock import AsyncMock, patch
import pytest

from app.ai.orchestration.planner import PlanResult, SubTask
from app.ai.orchestration.task_graph import TaskGraphExecutor


@pytest.mark.asyncio
async def test_dag_parallel_branch_concurrency():
    """Verify that independent tasks run concurrently and merge cleanly into downstream nodes."""
    executor = TaskGraphExecutor()

    # Plan with 2 independent root branches and 1 merge task
    plan = PlanResult(
        is_decomposition=True,
        goal="Fetch market research and compile financial data into a presentation",
        tasks=[
            SubTask(id="T1", agent="OMNI", title="Market Research", instruction="Gather market trends", depends_on=[]),
            SubTask(id="T2", agent="AXIS", title="Financial Computation", instruction="Compute profit margins", depends_on=[]),
            SubTask(id="T3", agent="KINESIS", title="Compile Document", instruction="Combine {T1.output} and {T2.output}", depends_on=["T1", "T2"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Synthesize {T3.output}"},
    )

    with patch("app.ai.agents.research_agent.research_agent.run", new_callable=AsyncMock) as mock_omni, \
         patch("app.ai.agents.coding_agent.coding_agent.run", new_callable=AsyncMock) as mock_axis, \
         patch("app.ai.agents.document_agent.document_agent.run", new_callable=AsyncMock) as mock_kinesis, \
         patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat:

        mock_omni.return_value = "OMNI: 2026 AI market up 45%."
        mock_axis.return_value = "AXIS: Margin computed at 34.2%."
        mock_kinesis.return_value = "KINESIS: Document generated successfully."
        mock_chat.return_value = "Synthesis: Executive summary complete."

        events = []
        async def on_event(ev, data):
            events.append(ev)

        result = await executor.execute_plan(plan, on_event=on_event)

        assert result.success is True
        assert len(result.tasks) == 3
        assert result.tasks[0].status == "done"
        assert result.tasks[1].status == "done"
        assert result.tasks[2].status == "done"
        assert "task_graph_start" in events
        assert "task_graph_complete" in events
        assert len(result.inter_agent_messages) >= 2


@pytest.mark.asyncio
async def test_dag_cyclic_dependency_rejection():
    """Verify that a cycle in task dependencies is cleanly detected and reported without deadlocking."""
    executor = TaskGraphExecutor()

    # T1 depends on T2, T2 depends on T1 (Cycle)
    plan = PlanResult(
        is_decomposition=True,
        goal="Test cyclic deadlock protection",
        tasks=[
            SubTask(id="T1", agent="OMNI", title="Task 1", instruction="Do 1", depends_on=["T2"]),
            SubTask(id="T2", agent="AXIS", title="Task 2", instruction="Do 2", depends_on=["T1"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Final"},
    )

    result = await executor.execute_plan(plan)

    assert result.success is False
    assert result.tasks[0].status == "failed"
    assert result.tasks[1].status == "failed"
    assert "cycle" in result.tasks[0].error.lower() or "unresolvable" in result.tasks[0].error.lower()


@pytest.mark.asyncio
async def test_dag_upstream_failure_cascade():
    """Verify that if an upstream task fails, downstream dependent tasks fail immediately instead of hanging."""
    executor = TaskGraphExecutor()

    plan = PlanResult(
        is_decomposition=True,
        goal="Test failure cascading",
        tasks=[
            SubTask(id="T1", agent="OMNI", title="Failing Task", instruction="Raise error", depends_on=[]),
            SubTask(id="T2", agent="KINESIS", title="Dependent Task", instruction="Use {T1.output}", depends_on=["T1"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Final"},
    )

    with patch("app.ai.agents.research_agent.research_agent.run", new_callable=AsyncMock) as mock_omni:
        mock_omni.side_effect = RuntimeError("Network timeout connecting to search provider")

        result = await executor.execute_plan(plan)

        assert result.success is False
        assert result.tasks[0].status == "failed"
        assert "Network timeout" in result.tasks[0].error
        assert result.tasks[1].status == "failed"
        assert "Dependency failed" in result.tasks[1].error


def test_task_graph_placeholder_substitution():
    """Verify placeholder string interpolation."""
    executor = TaskGraphExecutor()

    outputs = {
        "T1": "Apple Inc. Financials",
        "T2.output": "Growth is 12%",
        "custom_key": "Verified Data",
    }

    raw_instruction = "Summarize {T1.output} where {T2.output} and {custom_key}"
    substituted = executor._substitute_placeholders(raw_instruction, outputs)

    assert "Apple Inc. Financials" in substituted
    assert "Growth is 12%" in substituted
    assert "Verified Data" in substituted
