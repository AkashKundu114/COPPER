from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.ai.ambient.research_pipeline import research_pipeline, ResearchReport

router = APIRouter(prefix="/research", tags=["research"])

class StartResearchRequest(BaseModel):
    topic: str
    depth: Optional[str] = "standard"
    deadline: Optional[str] = None

@router.post("/start")
async def start_research(req: StartResearchRequest):
    report = await research_pipeline.start_research(req.topic, req.depth, req.deadline)
    return {"report_id": report.report_id, "status": report.status}

@router.get("/reports")
async def list_reports(status: Optional[str] = None, limit: int = Query(20, ge=1, le=100)):
    return research_pipeline.list_reports(status=status, limit=limit)

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = research_pipeline.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/reports/{report_id}/markdown")
async def get_report_markdown(report_id: str):
    report = research_pipeline.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"markdown_report": report.markdown_report}

@router.post("/reports/{report_id}/cancel")
async def cancel_research(report_id: str):
    success = research_pipeline.cancel_research(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found or not active")
    return {"status": "cancelled"}
