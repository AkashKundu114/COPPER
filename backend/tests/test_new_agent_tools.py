import json
import pytest
from pathlib import Path

from app.ai.agents.agency_catalog import (
    get_persona,
    inject_persona,
    list_personas,
)
from app.ai.tools.builtin.persona_tools import agency_persona_lookup
from app.ai.tools.builtin.codebase_tools import codebase_map, codebase_symbol_lookup
from app.ai.tools.builtin.git_tools import git_status, git_log
from app.ai.tools.builtin.system_tools import system_hardware_stats, process_status
from app.ai.tools.builtin.scrapling_tools import scrapling_scrape, _adaptive_content_extract
from app.ai.tools.builtin.science_tools import dataset_summary
from app.ai.tools.builtin.video_tools import video_create_slideshow
from app.ai.tools.builtin.diagram_tools import workflow_diagram_render, generate_mermaid_flowchart
from bs4 import BeautifulSoup


@pytest.mark.asyncio
async def test_codebase_mapping_and_symbol_lookup(tmp_path):
    # Create sample python files in tmp_path
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

    # Test codebase_map
    map_res = await codebase_map(root_path=str(tmp_path), max_depth=2, include_symbols=True)
    assert map_res["status"] == "success"
    assert map_res["total_files_scanned"] == 1
    assert map_res["total_symbols_indexed"] >= 2
    assert "sample_service.py" in map_res["tree"]
    tree_item = map_res["tree"]["sample_service.py"]
    assert len(tree_item["classes"]) == 1
    assert tree_item["classes"][0]["name"] == "CopperOptimizer"
    assert len(tree_item["functions"]) == 1
    assert tree_item["functions"][0]["name"] == "compute_cascade_risk"

    # Test codebase_symbol_lookup
    lookup_res = await codebase_symbol_lookup("CopperOptimizer", root_path=str(tmp_path))
    assert lookup_res["status"] == "success"
    assert lookup_res["total_matches"] == 1
    assert lookup_res["matches"][0]["type"] == "class"
    assert lookup_res["matches"][0]["file"] == "sample_service.py"

    fn_lookup = await codebase_symbol_lookup("compute_cascade_risk", root_path=str(tmp_path))
    assert fn_lookup["status"] == "success"
    assert fn_lookup["total_matches"] == 1
    assert fn_lookup["matches"][0]["is_async"] is True


@pytest.mark.asyncio
async def test_agency_catalog():
    # Test persona retrieval
    devops = get_persona("devops_engineer")
    assert devops is not None
    assert devops["domain"] == "engineering"

    # Test listing personas
    all_personas = list_personas()
    assert len(all_personas) >= 8

    sec_personas = list_personas("security")
    assert len(sec_personas) >= 1
    assert any(p["id"] == "security_pentester" for p in sec_personas)

    # Test persona prompt injection
    prompt = inject_persona("Base instructions.", "codebase_architect")
    assert "Software Systems Architect" in prompt
    assert "Base instructions." in prompt

    # Test agency_persona_lookup tool
    tool_res = await agency_persona_lookup(persona_id="data_scientist")
    assert tool_res["status"] == "success"
    assert tool_res["persona"]["title"] == "Senior Data Scientist & Statistician"


@pytest.mark.asyncio
async def test_git_tools():
    # Run against current project directory
    res = await git_status(repo_path=".")
    assert res["status"] in ["success", "error"]  # success if in git repo
    if res["status"] == "success":
        assert "branch" in res
        assert "changes" in res

    log_res = await git_log(repo_path=".", max_count=3)
    assert log_res["status"] in ["success", "error"]
    if log_res["status"] == "success":
        assert isinstance(log_res["commits"], list)


@pytest.mark.asyncio
async def test_system_tools():
    stats = await system_hardware_stats()
    assert stats["status"] == "success"
    assert "host" in stats
    assert "disk" in stats
    assert stats["disk"]["total_gb"] > 0

    procs = await process_status(filter_name="python", limit=5)
    assert procs["status"] in ["success", "warning"]


@pytest.mark.asyncio
async def test_scrapling_resilient_extraction():
    html = """
    <html>
      <head><title>Scrapling Test Article</title><meta name="description" content="Test description"/></head>
      <body>
        <div class="sidebar">Ads and navigation</div>
        <article class="main-content">
          <h1>Main Article Headline</h1>
          <p>This is a high quality test paragraph demonstrating resilient extraction without crashing.</p>
        </article>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    extracted = _adaptive_content_extract(soup, target_hint="main-content")
    assert "Main Article Headline" in extracted
    assert "high quality test paragraph" in extracted

    # Test invalid URL format
    res = await scrapling_scrape("not-a-valid-url")
    assert res["status"] == "error"
    assert "Invalid URL" in res["error"]


@pytest.mark.asyncio
async def test_dataset_summary(tmp_path):
    csv_file = tmp_path / "metrics.csv"
    csv_file.write_text("model,latency_ms,qps\nqwen-7b,12.5,80\nllama-8b,14.2,70\n", encoding="utf-8")

    res = await dataset_summary(str(csv_file))
    assert res["status"] == "success"
    assert res["total_rows"] == 2
    assert res["columns_count"] == 3
    assert "qps" in res["columns"]

    # Test JSON tabular format
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps([{"agent": "AXIS", "score": 98}, {"agent": "OMNI", "score": 95}]), encoding="utf-8")
    json_res = await dataset_summary(str(json_file))
    assert json_res["status"] == "success"
    assert json_res["total_rows"] == 2


@pytest.mark.asyncio
async def test_video_tools_validation():
    # Test missing images validation
    res = await video_create_slideshow(["nonexistent_image.png"], "out.mp4")
    assert res["status"] == "error"


@pytest.mark.asyncio
async def test_diagram_generator():
    steps = ["Load Codebase AST", "Scan for Vulnerabilities", "Report Findings"]
    res = await workflow_diagram_render(title="Security Audit DAG", steps=steps)
    assert res["status"] == "success"
    assert "```mermaid" in res["mermaid"]
    assert "Security Audit DAG" in res["mermaid"]
    assert "STEP_1" in res["mermaid"]
    assert "STEP_2" in res["mermaid"]
