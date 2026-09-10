from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.ai.workflows.dsl import (
    Workflow,
    workflow_store,
)
from app.ai.workflows.trigger_parser import trigger_parser
from app.ai.workflows.workflow_engine import workflow_engine
from app.core.logger import logger

router = APIRouter(prefix="/workflows", tags=["workflows"])


class CreateWorkflowRequest(BaseModel):
    prompt: str | None = Field(
        default=None,
        description="Natural language workflow prompt, e.g. 'Every morning at 9am, summarize my overdue tasks'",
    )
    workflow: dict[str, Any] | None = Field(
        default=None,
        description="Direct structured workflow definition JSON (optional)",
    )
    auto_enable: bool = Field(
        default=True,
        description="Whether to automatically enable and register the workflow",
    )


class ToggleWorkflowRequest(BaseModel):
    enabled: bool | None = Field(
        default=None,
        description="Set enabled status directly, or omit to toggle current status",
    )


@router.post("", status_code=200)
async def create_workflow(req: CreateWorkflowRequest):
    """
    Creates a new workflow either from a natural language prompt via DAEMON parser
    or from a pre-defined structured workflow definition.
    """
    # 1. Natural Language Prompt flow
    if req.prompt:
        parse_res = await trigger_parser.parse(req.prompt)
        if not parse_res.success:
            return {
                "status": "clarification_needed",
                "success": False,
                "questions": parse_res.questions,
                "error": parse_res.error,
                "raw": parse_res.raw_json,
            }

        wf = parse_res.workflow
        if not wf:
            raise HTTPException(status_code=400, detail="Failed to instantiate workflow from parsed prompt")

        wf.enabled = req.auto_enable
        created_wf = workflow_store.create(wf)
        if created_wf.enabled:
            workflow_engine.register_workflow(created_wf)

        return {
            "status": "created",
            "success": True,
            "workflow": created_wf.to_dict(),
        }

    # 2. Structured Workflow JSON flow
    elif req.workflow:
        try:
            wf = Workflow.from_dict(req.workflow)
            wf.enabled = req.auto_enable
            created_wf = workflow_store.create(wf)
            if created_wf.enabled:
                workflow_engine.register_workflow(created_wf)

            return {
                "status": "created",
                "success": True,
                "workflow": created_wf.to_dict(),
            }
        except Exception as e:
            logger.error(f"Error creating structured workflow: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid workflow structure: {str(e)}")

    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'prompt' or 'workflow' must be provided in request body.",
        )


@router.get("")
async def list_workflows(enabled_only: bool = Query(default=False, description="Filter for enabled workflows")):
    """Lists all stored workflows."""
    workflows = workflow_store.get_all(enabled_only=enabled_only)
    return [wf.to_dict() for wf in workflows]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Retrieves a single workflow by ID."""
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return wf.to_dict()


@router.put("/{workflow_id}/toggle")
async def toggle_workflow(workflow_id: str, req: ToggleWorkflowRequest | None = None):
    """Enables or disables a workflow, dynamically updating APScheduler registration."""
    target_enabled = req.enabled if req else None
    wf = workflow_store.toggle(workflow_id, target_enabled)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    if wf.enabled:
        workflow_engine.register_workflow(wf)
    else:
        workflow_engine.unregister_workflow(wf.id)

    return {
        "status": "toggled",
        "id": wf.id,
        "enabled": wf.enabled,
        "workflow": wf.to_dict(),
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Deletes a workflow and removes its scheduled jobs."""
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    workflow_engine.unregister_workflow(workflow_id)
    deleted = workflow_store.delete(workflow_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete workflow")

    return {"status": "deleted", "id": workflow_id}


@router.get("/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: str,
    limit: int = Query(default=50, ge=1, le=500, description="Max history entries to retrieve"),
):
    """Retrieves execution history records for a workflow."""
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    history = workflow_store.get_history(workflow_id, limit=limit)
    return [h.to_dict() for h in history]


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str):
    """Manually triggers an immediate execution of the workflow."""
    wf = workflow_store.get(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    record = await workflow_engine.execute_workflow(workflow_id)
    return {
        "status": "completed",
        "record": record.to_dict(),
    }
