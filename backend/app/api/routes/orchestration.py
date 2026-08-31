from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.orchestration.context_bus import context_bus
from app.ai.orchestration.planner import PlanResult, SubTask, nexus_planner
from app.ai.orchestration.task_graph import task_graph_executor
from app.core.logger import logger
from app.utils.helpers import generate_session_id

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


class PlanRequest(BaseModel):
    message: str = Field(..., description="User request to evaluate and decompose")
    context: str = Field("", description="Optional memory or profile context")


class ExecuteRequest(BaseModel):
    message: str = Field(..., description="User request to decompose and execute")
    session_id: str | None = Field(None, description="Optional session ID for WebSocket live telemetry")
    context: str = Field("", description="Optional memory context")


@router.post("/plan")
async def plan_task_decomposition(req: PlanRequest):
    """
    Decompose a complex request into a DAG of sub-tasks using DeepSeek-R1 reasoning.
    """
    try:
        plan = await nexus_planner.plan(req.message, req.context)
        return plan.to_dict()
    except Exception as e:
        logger.error(f"Orchestration plan route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_task_graph(req: ExecuteRequest):
    """
    Execute a collaborative multi-agent workflow for a complex task.
    Dispatches tasks in parallel/sequence, shares state across the ContextBus,
    and synthesizes results.
    """
    session_id = req.session_id or generate_session_id()
    try:
        plan = await nexus_planner.plan(req.message, req.context)
        if not plan.is_decomposition:
            return {
                "is_decomposition": False,
                "target_agent": plan.target_agent,
                "message": "Single-agent execution recommended.",
            }

        result = await task_graph_executor.execute_plan(
            plan=plan,
            memory_context=req.context,
            session_id=session_id,
        )
        return result.to_dict()
    except Exception as e:
        logger.error(f"Orchestration execute route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces")
async def list_traces(limit: int = 50):
    """
    Fetch recent multi-agent collaborative DAG execution traces.
    """
    return context_bus.list_traces(limit=limit)


@router.get("/trace/{dag_id}")
async def get_trace(dag_id: str):
    """
    Fetch detailed trace for a specific DAG execution run including inter-agent messages.
    """
    trace = context_bus.get_trace(dag_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace
