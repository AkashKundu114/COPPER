import pytest
from app.ai.agents.document_agent import document_agent
from app.core.constants import AgentType


def test_document_agent_format_detection():
    assert document_agent._detect_format("Create a PDF report on machine learning") == "pdf"
    assert document_agent._detect_format("Generate a Word document proposal") == "docx"
    assert document_agent._detect_format("Build a presentation slide deck for the pitch") == "pptx"
    assert document_agent._detect_format("Turn this into an excel workbook") == "xlsx"
    assert document_agent._detect_format("Export data to csv spreadsheet") == "csv"
    assert document_agent._detect_format("Write a markdown spec") == "md"
    assert document_agent._detect_format("Create an html webpage summary") == "html"
    assert document_agent._detect_format("Export as json data") == "json"


def test_document_agent_template_detection():
    assert document_agent._detect_template("Write a project proposal for our mobile app") == "project_proposal"
    assert document_agent._detect_template("Create an executive summary for Q4") == "executive_summary"
    assert document_agent._detect_template("Meeting notes and minutes from standup") == "meeting_notes"
    assert document_agent._detect_template("Build a professional resume CV") == "resume"
    assert document_agent._detect_template("Generate an invoice table sheet") == "invoice_table"


@pytest.mark.asyncio
async def test_document_agent_run_resilient():
    result = await document_agent.run(
        message="Create a PDF report on Artificial Intelligence",
        history=[],
        memory_context="User is exploring AI architectures.",
    )
    assert result is not None
    assert "Document Artifact Created Successfully" in result or "Generated document" in result
