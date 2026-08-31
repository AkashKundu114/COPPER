import pytest
from pathlib import Path
from app.services.document_service import DocumentService


@pytest.fixture
def doc_service(tmp_path):
    return DocumentService(output_dir=str(tmp_path / "test_docs"))


def test_document_service_templates(doc_service):
    templates = doc_service.DOCUMENT_TEMPLATES
    assert len(templates) >= 6
    assert "technical_report" in templates
    assert "project_proposal" in templates
    assert "executive_summary" in templates
    assert "meeting_notes" in templates


def test_generate_pdf(doc_service):
    title = "Test Quantum Computing Report"
    sections = [
        {"heading": "Executive Summary", "content": "Overview of quantum state space."},
        {"heading": "Architecture", "bullets": ["Qubit superposition", "Quantum entanglement"]},
        {
            "heading": "Metrics",
            "table": {
                "headers": ["Metric", "Classical", "Quantum"],
                "rows": [["Search Speed", "O(N)", "O(sqrt(N))"], ["Factoring", "Exponential", "Polynomial"]],
            },
        },
    ]
    pdf_bytes, out_path = doc_service.generate_pdf(title=title, sections=sections)
    assert len(pdf_bytes) > 100
    assert out_path.exists()
    assert out_path.suffix == ".pdf"


def test_generate_docx(doc_service):
    title = "Project Scope Document"
    sections = [
        {"heading": "Objectives", "content": "Deliver scalable AI orchestration."},
        {"subheading": "Milestones", "bullets": ["Phase 1: Router", "Phase 2: Documents"]},
        {
            "heading": "Deliverables",
            "table": {
                "headers": ["Module", "Format", "Status"],
                "rows": [["ReportLab", "PDF", "Completed"], ["python-docx", "DOCX", "Completed"]],
            },
        },
    ]
    docx_bytes, out_path = doc_service.generate_docx(title=title, sections=sections)
    assert len(docx_bytes) > 500
    assert out_path.exists()
    assert out_path.suffix == ".docx"


def test_generate_pptx(doc_service):
    title = "C.O.P.P.E.R. Architecture Deck"
    sections = [
        {"heading": "System Architecture", "bullets": ["Tiered Inference", "Gatekeeper Model", "Dynamic Routing"]},
        {"heading": "VRAM Discipline", "content": "Gatekeeper pinned at keep_alive=-1, heavy models swept after idle."},
    ]
    pptx_bytes, out_path = doc_service.generate_pptx(title=title, sections=sections)
    assert len(pptx_bytes) > 50
    assert out_path.exists()
    assert out_path.suffix == ".pptx"


def test_generate_xlsx(doc_service):
    title = "Model Inventory & VRAM Budget"
    headers = ["Model", "Role", "VRAM (GB)", "Keep-Alive"]
    rows = [
        ["Qwen2.5-0.5B", "Gatekeeper", "0.38", "-1"],
        ["Llama-3.1-8B", "Chat Core", "4.58", "240s"],
        ["Qwen2.5-Coder-7B", "AXIS Coding", "4.36", "240s"],
    ]
    xlsx_bytes, out_path = doc_service.generate_xlsx(title=title, headers=headers, rows=rows)
    assert len(xlsx_bytes) > 50
    assert out_path.exists()
    assert out_path.suffix == ".xlsx"


def test_generate_markdown(doc_service):
    title = "API Specification"
    sections = [
        {"heading": "Overview", "content": "RESTful endpoints for C.O.P.P.E.R."},
        {"heading": "Endpoints", "bullets": ["GET /documents", "POST /documents/generate"]},
        {
            "heading": "Status Codes",
            "table": {
                "headers": ["Code", "Meaning"],
                "rows": [["200", "OK"], ["400", "Bad Request"]],
            },
        },
    ]
    md_text, out_path = doc_service.generate_markdown(title=title, sections=sections)
    assert "# API Specification" in md_text
    assert "RESTful endpoints" in md_text
    assert out_path.exists()


def test_generate_html(doc_service):
    title = "Interactive System Dashboard"
    sections = [
        {"heading": "System Health", "content": "All models operational."},
        {"heading": "Active Agents", "bullets": ["KINESIS Document Architect", "Mini Router"]},
    ]
    html_text, out_path = doc_service.generate_html(title=title, sections=sections)
    assert "<!DOCTYPE html>" in html_text
    assert "Interactive System Dashboard" in html_text
    assert "KINESIS Document Architect" in html_text
    assert out_path.exists()


def test_generate_csv_and_tsv(doc_service):
    headers = ["ID", "Name", "Score"]
    rows = [["1", "Alice", "98"], ["2", "Bob", "95"]]
    
    csv_text, csv_path = doc_service.generate_csv(headers=headers, rows=rows)
    assert "ID,Name,Score" in csv_text
    assert csv_path.exists()

    tsv_text, tsv_path = doc_service.generate_tsv(headers=headers, rows=rows)
    assert "ID	Name	Score" in tsv_text
    assert tsv_path.exists()


def test_generate_json(doc_service):
    data = {"system": "COPPER", "version": "1.1", "active": True}
    json_text, json_path = doc_service.generate_json(data=data)
    assert '"system": "COPPER"' in json_text
    assert json_path.exists()


@pytest.mark.asyncio
async def test_create_document_high_level(doc_service):
    meta = await doc_service.create_document(
        format="pdf",
        title="High-Level Architecture Document",
        raw_content="Executive summary for the AI platform.",
        template_type="technical_report",
        index_to_memory=False,
    )
    assert meta["status"] == "success"
    assert meta["format"] == "pdf"
    assert meta["title"] == "High-Level Architecture Document"
    assert Path(meta["filepath"]).exists()

    # Verify listing and safe path retrieval
    docs = doc_service.list_generated_documents()
    assert len(docs) >= 1
    assert any(d["filename"] == meta["filename"] for d in docs)

    resolved = doc_service.get_document_file_path(meta["filename"])
    assert resolved is not None
    assert resolved.exists()
