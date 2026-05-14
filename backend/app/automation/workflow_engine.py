import asyncio
from typing import Callable, Any
from app.core.logger import logger


class WorkflowStep:
    def __init__(self, name: str, func: Callable, args: list = None, kwargs: dict = None):
        self.name = name
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}

    async def execute(self) -> Any:
        logger.info(f"Executing step: {self.name}")
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(*self.args, **self.kwargs)
        return self.func(*self.args, **self.kwargs)


class Workflow:
    def __init__(self, name: str):
        self.name = name
        self.steps: list[WorkflowStep] = []
        self.results: list[dict] = []
        self._on_step_complete: Callable = None

    def add_step(self, name: str, func: Callable, args: list = None, kwargs: dict = None):
        self.steps.append(WorkflowStep(name, func, args, kwargs))
        return self

    def on_step_complete(self, callback: Callable):
        self._on_step_complete = callback
        return self

    async def run(self, stop_on_error: bool = True) -> dict:
        logger.info(f"Starting workflow: {self.name}")
        self.results = []
        success_count = 0

        for i, step in enumerate(self.steps):
            try:
                result = await step.execute()
                self.results.append({
                    "step": step.name,
                    "success": True,
                    "result": result,
                })
                success_count += 1
                if self._on_step_complete:
                    await self._on_step_complete(i, step.name, True, result)
            except Exception as e:
                logger.error(f"Workflow step '{step.name}' failed: {e}")
                self.results.append({
                    "step": step.name,
                    "success": False,
                    "error": str(e),
                })
                if self._on_step_complete:
                    await self._on_step_complete(i, step.name, False, None)
                if stop_on_error:
                    break

        total = len(self.steps)
        completed = len(self.results)
        logger.info(f"Workflow '{self.name}' done: {success_count}/{total} steps succeeded")
        return {
            "workflow": self.name,
            "total_steps": total,
            "completed_steps": completed,
            "success_count": success_count,
            "results": self.results,
            "success": success_count == total,
        }


# Pre-built workflow templates
async def organize_downloads_workflow(downloads_path: str, output_path: str) -> dict:
    from app.automation.file_manager import list_directory, move_file, create_directory

    EXTENSIONS = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".pptx"],
        "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml"],
        "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    }

    files = await list_directory(downloads_path)
    moved = 0

    for file in files:
        if file["is_dir"]:
            continue
        ext = file["name"].rsplit(".", 1)[-1].lower()
        ext_with_dot = f".{ext}"

        target_folder = "Other"
        for folder, extensions in EXTENSIONS.items():
            if ext_with_dot in extensions:
                target_folder = folder
                break

        target_dir = f"{output_path}/{target_folder}"
        await create_directory(target_dir)
        if await move_file(file["path"], f"{target_dir}/{file['name']}"):
            moved += 1

    return {"files_organized": moved, "source": downloads_path, "destination": output_path}
