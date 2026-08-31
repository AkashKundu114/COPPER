from unittest.mock import AsyncMock, patch
import pytest

from app.ai.orchestration.planner import NexusPlanner, PlanResult, SubTask, nexus_planner
from app.ai.orchestration.task_graph import TaskGraphExecutor, task_graph_executor


def test_nexus_planner_heuristics():
    planner = NexusPlanner()

    # Simple prompt should not trigger decomposition
    assert planner.should_consider_decomposition("Hello, what is the weather?") is False

    # Multi-step complex queries
    assert planner.should_consider_decomposition(
        "Analyze this CSV sales data, write a Python script to visualize trends, and create a PDF report with the findings"
    ) is True

    complex_prompt = "First research the latest vector index algorithms, and then write a python benchmark script to test them, and finally schedule a reminder for me."
    assert planner.should_consider_decomposition(complex_prompt) is True


def test_parse_plan_single_agent():
    planner = NexusPlanner()
    raw = "<plan>SINGLE_AGENT: AXIS</plan>"
    res = planner._parse_plan_output(raw)
    assert res.is_decomposition is False
    assert res.target_agent == "axis"


def test_parse_plan_deepseek_r1_with_thinking():
    planner = NexusPlanner()
    raw = """<think>
The user wants to analyze CSV data, plot trends with python, and generate a PDF report.
This is a multi-step task requiring:
1. OMNI for data extraction
2. AXIS for matplotlib code
3. FORGE for executing the script and capturing the image
4. KINESIS for authoring the PDF report.
</think>
<plan>
{
  "goal": "Analyze sales data, visualize trends via Python, and generate a comprehensive PDF executive report",
  "tasks": [
    {
      "id": "T1",
      "agent": "OMNI",
      "title": "Analyze CSV Data & Extract Key Insights",
      "instruction": "Analyze the sales CSV data and extract quarterly metrics.",
      "depends_on": [],
      "output_key": "sales_insights"
    },
    {
      "id": "T2",
      "agent": "AXIS",
      "title": "Author Matplotlib Visualization Script",
      "instruction": "Write a Python script using matplotlib based on {T1.output}.",
      "depends_on": ["T1"],
      "output_key": "plot_script"
    },
    {
      "id": "T2.1",
      "agent": "FORGE",
      "title": "Execute Plot Script in Sandbox & Capture Chart",
      "instruction": "Execute {T2.output} in the sandbox.",
      "depends_on": ["T2"],
      "output_key": "chart_artifact"
    },
    {
      "id": "T3",
      "agent": "KINESIS",
      "title": "Generate Final PDF Executive Report",
      "instruction": "Generate PDF report combining {T1.output} and {T2.1.output}.",
      "depends_on": ["T1", "T2.1"],
      "output_key": "pdf_report"
    }
  ],
  "synthesis": {
    "agent": "CHAT",
    "instruction": "Synthesize all findings from {T1.output}, {T2.output}, and {T3.output} into a polished summary."
  }
}
</plan>"""
    res = planner._parse_plan_output(raw)
    assert res.is_decomposition is True
    assert "OMNI for data extraction" in res.thinking
    assert len(res.tasks) == 4
    assert res.tasks[0].id == "T1"
    assert res.tasks[0].agent == "OMNI"
    assert res.tasks[2].id == "T2.1"
    assert res.tasks[2].agent == "FORGE"
    assert res.tasks[2].depends_on == ["T2"]
    assert res.tasks[3].id == "T3"
    assert res.tasks[3].depends_on == ["T1", "T2.1"]


@pytest.mark.asyncio
async def test_task_graph_execution_parallel_and_dependent():
    executor = TaskGraphExecutor()

    plan = PlanResult(
        is_decomposition=True,
        goal="Analyze CSV and create report",
        tasks=[
            SubTask(id="T1", agent="OMNI", title="Analyze CSV", instruction="Step 1 data", depends_on=[]),
            SubTask(id="T2", agent="AXIS", title="Generate Script", instruction="Step 2 code using {T1.output}", depends_on=["T1"]),
            SubTask(id="T2.1", agent="FORGE", title="Run Sandbox", instruction="Step 2.1 run {T2.output}", depends_on=["T2"]),
            SubTask(id="T3", agent="KINESIS", title="Build PDF", instruction="Step 3 PDF from {T1.output} and {T2.1.output}", depends_on=["T1", "T2.1"]),
        ],
        synthesis={"agent": "CHAT", "instruction": "Combine {T1.output} and {T3.output}"},
    )

    with patch("app.ai.agents.research_agent.research_agent.run", new_callable=AsyncMock) as mock_omni, \
         patch("app.ai.agents.coding_agent.coding_agent.run", new_callable=AsyncMock) as mock_axis, \
         patch("app.ai.agents.document_agent.document_agent.run", new_callable=AsyncMock) as mock_kinesis, \
         patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat, \
         patch("app.core.forge_sandbox.forge_sandbox.execute_python") as mock_sandbox:

        mock_omni.return_value = "OMNI: Identified 28% sales growth in Q3."
        mock_axis.return_value = "AXIS: ```python\nimport matplotlib.pyplot as plt\nplt.plot([1,2,3])\n```"
        mock_sandbox.return_value = {"status": "success", "stdout": "Plot saved to sales_trend.png"}
        mock_kinesis.return_value = "KINESIS: Document Artifact Created Successfully [sales_report.pdf](/docs/sales_report.pdf)"
        mock_chat.return_value = "NEXUS Final Synthesis: Complete sales report and visualizations generated."

        events = []
        async def on_event(ev_type, data):
            events.append(ev_type)

        res = await executor.execute_plan(plan, memory_context="TestContext", on_event=on_event)

        assert res.success is True
        assert "NEXUS Final Synthesis" in res.final_response
        assert len(res.tasks) == 4
        assert res.tasks[0].status == "done"
        assert res.tasks[1].status == "done"
        assert res.tasks[2].status == "done"
        assert res.tasks[3].status == "done"
        assert len(res.inter_agent_messages) >= 3
        assert "task_graph_start" in events
        assert "task_graph_complete" in events
