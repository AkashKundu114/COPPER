from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.automation_service import automation_service
from app.core.logger import logger

router = APIRouter(prefix="/automation", tags=["automation"])


class CommandRequest(BaseModel):
    command: str


class AppRequest(BaseModel):
    app_name: str
    args: list[str] = []


class UrlRequest(BaseModel):
    url: str


class FileOperationRequest(BaseModel):
    operation: str
    src: Optional[str] = None
    dst: Optional[str] = None
    path: Optional[str] = None
    pattern: Optional[str] = None
    directory: Optional[str] = None
    safe: bool = True


class TaskRequest(BaseModel):
    task: str


class WorkflowRequest(BaseModel):
    steps: list[dict]


class OrganizeRequest(BaseModel):
    source: str
    destination: str


@router.get("/system/stats")
async def system_stats():
    return await automation_service.get_system_stats()


@router.get("/system/processes")
async def get_processes():
    return await automation_service.get_processes()


@router.post("/system/command")
async def run_command(req: CommandRequest):
    # Basic security: reject obviously dangerous commands
    dangerous = ["rm -rf /", "format", "mkfs", "dd if=/dev/zero"]
    if any(d in req.command.lower() for d in dangerous):
        raise HTTPException(status_code=403, detail="Command not allowed")
    return await automation_service.execute_command(req.command)


@router.post("/app/launch")
async def launch_app(req: AppRequest):
    success = await automation_service.open_app(req.app_name)
    return {"success": success, "app": req.app_name}


@router.post("/app/url")
async def open_url(req: UrlRequest):
    success = await automation_service.open_url(req.url)
    return {"success": success, "url": req.url}


@router.get("/windows")
async def list_windows():
    return await automation_service.list_windows()


@router.get("/files/browse")
async def browse_directory(path: str = "."):
    return await automation_service.browse_directory(path)


@router.post("/files/operation")
async def file_operation(req: FileOperationRequest):
    kwargs = req.dict(exclude_none=True, exclude={"operation"})
    return await automation_service.file_operation(req.operation, **kwargs)


@router.post("/files/organize")
async def organize_files(req: OrganizeRequest):
    return await automation_service.organize_files(req.source, req.destination)


@router.post("/task/plan")
async def plan_task(req: TaskRequest):
    return await automation_service.plan_and_run(req.task)


@router.post("/workflow/run")
async def run_workflow(req: WorkflowRequest):
    return await automation_service.run_workflow(req.steps)
