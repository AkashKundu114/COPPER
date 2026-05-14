from typing import Optional
from app.automation.system_control import get_system_info, run_command, get_running_processes
from app.automation.app_control import launch_app, launch_url, list_open_windows
from app.automation.file_manager import (
    list_directory, copy_file, move_file, delete_file, search_files, get_file_info
)
from app.automation.workflow_engine import Workflow, organize_downloads_workflow
from app.ai.agents.automation_agent import automation_agent
from app.core.logger import logger


class AutomationService:
    async def get_system_stats(self) -> dict:
        return await get_system_info()

    async def execute_command(self, command: str) -> dict:
        logger.info(f"Executing command: {command[:80]}")
        return await run_command(command)

    async def get_processes(self) -> list[dict]:
        return await get_running_processes()

    async def open_app(self, app_name: str) -> bool:
        return await launch_app(app_name)

    async def open_url(self, url: str) -> bool:
        return await launch_url(url)

    async def list_windows(self) -> list[str]:
        return await list_open_windows()

    async def browse_directory(self, path: str) -> list[dict]:
        return await list_directory(path)

    async def file_operation(self, operation: str, **kwargs) -> dict:
        ops = {
            "copy": copy_file,
            "move": move_file,
            "delete": delete_file,
            "search": search_files,
            "info": get_file_info,
        }
        func = ops.get(operation)
        if not func:
            return {"success": False, "error": f"Unknown operation: {operation}"}
        try:
            result = await func(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def plan_and_run(self, task: str) -> dict:
        plan = await automation_agent.plan_automation(task)
        return {"plan": plan, "status": "planned"}

    async def organize_files(self, source: str, destination: str) -> dict:
        return await organize_downloads_workflow(source, destination)

    async def run_workflow(self, steps: list[dict]) -> dict:
        wf = Workflow("custom_workflow")
        for step in steps:
            func_map = {
                "run_command": run_command,
                "launch_app": launch_app,
                "open_url": launch_url,
            }
            func = func_map.get(step.get("action"))
            if func:
                wf.add_step(
                    step.get("name", step["action"]),
                    func,
                    args=step.get("args", []),
                )
        return await wf.run()


automation_service = AutomationService()
