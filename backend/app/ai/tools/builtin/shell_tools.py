import platform
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.forge_sandbox import forge_sandbox
from app.core.logger import logger
from app.core.os_executor import execute_powershell


@tool_registry.tool(
    name="shell_execute",
    description="Execute an OS shell command (PowerShell on Windows, Bash on Linux/macOS) directly on the host system.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The exact shell command line string to execute."},
            "timeout": {"type": "integer", "description": "Maximum execution timeout in seconds (default 30)."},
        },
        "required": ["command"],
    },
    return_description="Dictionary with stdout, stderr, and exit_code.",
    guardian_level=3,  # SAFETY
)
async def shell_execute(command: str, timeout: int = 30) -> dict[str, Any]:
    try:
        logger.info(f"Executing shell command: {command[:100]}")
        out = await execute_powershell(command, timeout=timeout)
        is_err = out.startswith("[Error]") or out.startswith("[System Error]") or out.startswith("[Execution Timeout")
        return {
            "status": "error" if is_err else "success",
            "command": command,
            "output": out,
            "exit_code": 1 if is_err else 0,
        }
    except Exception as e:
        logger.error(f"shell_execute failed: {e}")
        return {"status": "error", "command": command, "output": str(e), "exit_code": 1}


@tool_registry.tool(
    name="python_execute",
    description="Execute Python code inside the isolated Forge Sandbox environment and capture stdout/stderr.",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python source code to execute."},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)."},
        },
        "required": ["code"],
    },
    return_description="Dictionary containing stdout, stderr, and exit_code.",
    guardian_level=2,  # CHALLENGE
)
async def python_execute(code: str, timeout: int = 10) -> dict[str, Any]:
    try:
        logger.info(f"Executing Python code in Forge Sandbox ({len(code)} bytes)")
        res = forge_sandbox.run_python_code(code, timeout=timeout)
        return {
            "status": "success" if res["exit_code"] == 0 else "error",
            "stdout": res["stdout"],
            "stderr": res["stderr"],
            "exit_code": res["exit_code"],
            "error": res.get("error"),
        }
    except Exception as e:
        logger.error(f"python_execute error: {e}")
        return {"status": "error", "stdout": "", "stderr": str(e), "exit_code": 1, "error": str(e)}
