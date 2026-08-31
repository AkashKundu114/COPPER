from unittest.mock import AsyncMock, patch
import pytest

from app.ai.orchestration.planner import NexusPlanner, PlanResult, SubTask, nexus_planner
from app.ai.orchestration.task_graph import TaskGraphExecutor, task_graph_executor


def test_nexus_planner_heuristics():
    planner = NexusPlanner()

    # Simple prompt should not trigger decomposition
    assert planner.should_consider_decomposition("Hello, what is the weather?") is False

    # Multi-step complex query should trigger decomposition consideration
    complex_prompt = "First research the latest vector index algorithms, and then write a python benchmark script to test them, and finally schedule a reminder for me."
    assert planner.should_consider_decomposition(complex_prompt) is True


def test_parse_plan_single_agent():
    planner = NexusPlanner()
    raw = "<plan>SINGLE_AGENT: AXIS</plan>"
    res = planner._parse_plan_output(raw)
    assert res.is_decomposition is False
    assert res.target_agent == "axis"


def test_parse_plan_dag_json():
    planner = NexusPlanner()
    raw = """<plan>
{
  "goal": "Research and implement caching",
  "tasks": [
    {"id": "T1", "agent": "OMNI", "instruction": "Research LRU cache algorithms", "depends_on": []},
    {"id": "T2", "agent": "AXIS", "instruction": "Implement LRU in Python using {T1.output}", "depends_on": ["T1"]}
  ],
  "synthesis": {"agent": "CHAT", "instruction": "Summarize {T1.output} and {T2.output}"}
}
</plan>"""
    res = planner._parse_plan_output(raw)
    assert res.is_decomposition is True
    assert len(res.tasks) == 2
    assert res.tasks[0].id == "T1"
    assert res.tasks[0].agent == "OMNI"
    assert res.tasks[1].depends_on == ["T1"]


@pytest.mark.asyncio
async def test_task_graph_execution_parallel_and_dependent():
    executor = TaskGraphExecutor()

    plan = PlanResult(
        is_decomposition=True,
        goal="Collaborative Test",
        tasks=[
            SubTask(id="T1", agent="OMNI", instruction="Step 1 data", depends_on=[]),
            SubTask(id="T2", agent="AXIS", instruction="Step 2 process {T1.output}", depends_on=["T1"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Combine {T1.output} and {T2.output}"},
    )

    with patch("app.ai.agents.research_agent.research_agent.run", new_callable=AsyncMock) as mock_omni, \
         patch("app.ai.agents.coding_agent.coding_agent.run", new_callable=AsyncMock) as mock_axis, \
         patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat:

        mock_omni.return_value = "OMNI Research: Found optimal algorithm."
        mock_axis.return_value = "AXIS Code: def solve(): return True"
        mock_chat.return_value = "NEXUS Final Synthesis: Solution delivered."

        events = []
        async def on_event(ev_type, data):
            events.append(ev_type)

        res = await executor.execute_plan(plan, memory_context="TestContext", on_event=on_event)

        assert res.success is True
        assert "NEXUS Final Synthesis" in res.final_response
        assert len(res.tasks) == 2
        assert res.tasks[0].status == "done"
        assert res.tasks[1].status == "done"
        assert "task_graph_start" in events
        assert "task_graph_complete" in events
