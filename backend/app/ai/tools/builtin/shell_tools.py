import asyncio
import os
import shutil
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.forge_sandbox import forge_sandbox
from app.core.logger import logger


def _shell_command(command: str) -> list[str]:
    if os.name == "nt":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            return [powershell, "-NoProfile", "-NonInteractive", "-Command", command]
        return ["cmd.exe", "/d", "/c", command]

    shell = shutil.which("bash") or shutil.which("sh") or "sh"
    return [shell, "-c", command]


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
        process = await asyncio.create_subprocess_exec(
            *_shell_command(command),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError:
            process.kill()
            return {
                "status": "error",
                "command": command,
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "exit_code": 124,
            }

        return {
            "status": "success" if process.returncode == 0 else "error",
            "command": command,
            "output": stdout.decode(errors="replace"),
            "error": stderr.decode(errors="replace"),
            "exit_code": process.returncode,
        }
    except Exception as exc:
        logger.error(f"shell_execute failed: {exc}")
        return {
            "status": "error",
            "command": command,
            "output": "",
            "error": str(exc),
            "exit_code": 1,
        }


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
