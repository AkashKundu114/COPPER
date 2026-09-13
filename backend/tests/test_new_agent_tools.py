import json
import pytest
from pathlib import Path

from app.ai.agents.agency_catalog import (
    get_persona,
    inject_persona,
    list_personas,
    list_divisions,
    _load_catalog,
)
from app.ai.tools.builtin.persona_tools import agency_persona_lookup
from app.ai.tools.builtin.codebase_tools import codebase_map, codebase_symbol_lookup
from app.ai.tools.builtin.git_tools import git_status, git_log
from app.ai.tools.builtin.system_tools import system_hardware_stats, process_status
from app.ai.tools.builtin.scrapling_tools import scrapling_scrape, _adaptive_content_extract
from app.ai.tools.builtin.science_tools import dataset_summary
from app.ai.tools.builtin.science_catalog_tools import scientific_skill_lookup, scientific_skill_list
from app.ai.tools.builtin.video_tools import video_create_slideshow, video_pipeline_list
from app.ai.tools.builtin.diagram_tools import workflow_diagram_render, generate_mermaid_flowchart
from bs4 import BeautifulSoup


@pytest.mark.asyncio
async def test_codebase_mapping_and_symbol_lookup(tmp_path):
    mod = tmp_path / "sample_service.py"
    mod.write_text(
        '"""Sample service module."""\n\n'
        "class CopperOptimizer:\n"
        '    """Core optimizer."""\n'
        "    def optimize_fleet(self, qps: int):\n"
        "        return qps * 2\n\n"
        "async def compute_cascade_risk(dag_id: str):\n"
        '    """Compute cascade failure probability."""\n'
        "    return 0.05\n",
        encoding="utf-8",
    )

    map_res = await codebase_map(root_path=str(tmp_path), max_depth=2, include_symbols=True)
    assert map_res["status"] == "success"
    assert map_res["total_files_scanned"] == 1
    assert map_res["total_symbols_indexed"] >= 2
    assert "sample_service.py" in map_res["tree"]

    lookup_res = await codebase_symbol_lookup("CopperOptimizer", root_path=str(tmp_path))
    assert lookup_res["status"] == "success"
    assert lookup_res["total_matches"] == 1
    assert lookup_res["matches"][0]["type"] == "class"


@pytest.mark.asyncio
async def test_agency_catalog_full():
    cat = _load_catalog()
    assert len(cat) >= 250  # Over 260 agents compiled

    divs = list_divisions()
    assert len(divs) >= 15
    assert "engineering" in divs
    assert "security" in divs

    # Lookup by full ID
    arch = get_persona("engineering:engineering-software-architect")
    assert arch is not None
    assert "Software Architect" in arch["name"]

    # Lookup by partial slug
    sec = get_persona("engineering-devops-automator")
    assert sec is not None

    # Prompt injection
    injected = inject_persona("You are base assistant.", "engineering:engineering-software-architect")
    assert "[SPECIALIST PERSONA ACTIVE:" in injected

    # Tool lookup
    tool_res = await agency_persona_lookup(domain="engineering")
    assert tool_res["status"] == "success"
    assert len(tool_res["personas"]) > 0


@pytest.mark.asyncio
async def test_scientific_skills_catalog():
    # 165 scientific skills test
    bio_res = await scientific_skill_lookup("biopython")
    assert bio_res["status"] == "success"
    assert "biopython" in bio_res["skill"]["name"].lower()
    assert len(bio_res["skill"]["instructions"]) > 50

    rdkit_res = await scientific_skill_lookup("rdkit")
    assert rdkit_res["status"] == "success"

    # List skills
    list_res = await scientific_skill_list(filter_query="data", limit=10)
    assert list_res["status"] == "success"
    assert list_res["returned"] > 0
    assert list_res["total_available"] >= 160


@pytest.mark.asyncio
async def test_git_tools():
    res = await git_status(repo_path=".")
    assert res["status"] in ["success", "error"]

    log_res = await git_log(repo_path=".", max_count=3)
    assert log_res["status"] in ["success", "error"]


@pytest.mark.asyncio
async def test_system_tools():
    stats = await system_hardware_stats()
    assert stats["status"] == "success"
    assert "disk" in stats
    assert stats["disk"]["total_gb"] > 0


@pytest.mark.asyncio
async def test_scrapling_resilient_extraction():
    html = """
    <html>
      <head><title>Test Article</title></head>
      <body>
        <article class="main-content">
          <h1>Resilient Header</h1>
          <p>Scrapling resilient extraction test content.</p>
        </article>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    extracted = _adaptive_content_extract(soup, target_hint="main-content")
    assert "Resilient Header" in extracted

    res = await scrapling_scrape("invalid://url")
    assert res["status"] == "error"


@pytest.mark.asyncio
async def test_dataset_summary(tmp_path):
    csv_file = tmp_path / "metrics.csv"
    csv_file.write_text("model,latency_ms\nqwen,12.5\n", encoding="utf-8")
    res = await dataset_summary(str(csv_file))
    assert res["status"] == "success"
    assert res["total_rows"] == 1


@pytest.mark.asyncio
async def test_video_and_openmontage_pipelines():
    # Test pipeline list
    pipe_res = await video_pipeline_list()
    assert pipe_res["status"] == "success"
    assert "screen-demo" in pipe_res["pipelines"]
    assert "clip-factory" in pipe_res["pipelines"]

    # Test error handling on missing files
    res = await video_create_slideshow(["missing.png"], "out.mp4", pipeline="screen-demo")
    assert res["status"] == "error"


@pytest.mark.asyncio
async def test_diagram_generator_multi_types():
    # 1. Flowchart
    flow_res = await workflow_diagram_render(title="DAG Test", steps=["Step 1", "Step 2"])
    assert flow_res["status"] == "success"
    assert "graph TD" in flow_res["raw_code"]

    # 2. Sequence diagram
    seq_res = await workflow_diagram_render(
        title="Agent Handoff",
        diagram_type="sequence",
        participants=["User", "Router", "AXIS"],
        sequence_messages=[
            {"from": "User", "to": "Router", "text": "Build feature"},
            {"from": "Router", "to": "AXIS", "text": "Dispatch coding task"},
            {"from": "AXIS", "to": "User", "text": "Feature completed", "is_response": True},
        ],
    )
    assert seq_res["status"] == "success"
    assert "sequenceDiagram" in seq_res["raw_code"]
    assert "User->>Router: Build feature" in seq_res["raw_code"]

    # 3. ER Diagram
    er_res = await workflow_diagram_render(
        title="Database Schema",
        diagram_type="er_diagram",
        tables=[
            {
                "name": "UserMemory",
                "columns": [
                    {"name": "id", "type": "int", "pk": True},
                    {"name": "content", "type": "string"},
                ],
            }
        ],
    )
    assert er_res["status"] == "success"
    assert "erDiagram" in er_res["raw_code"]
    assert "UserMemory" in er_res["raw_code"]
