import asyncio
import os
import shutil

from app.core.logger import logger


def _get_shell_command(command: str) -> list[str]:
    if os.name == "nt":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            return [powershell, "-NoProfile", "-NonInteractive", "-Command", command]
        return ["cmd.exe", "/d", "/c", command]

    shell = shutil.which("bash") or shutil.which("sh") or "sh"
    return [shell, "-c", command]


async def execute_powershell(command: str, timeout: int = 30) -> str:
    """Executes a shell command directly on the host OS using the platform shell."""
    try:
        process = await asyncio.create_subprocess_exec(
            *_get_shell_command(command),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except TimeoutError:
            process.kill()
            return "[Execution Timeout Error] Command exceeded 30 seconds."

        out = stdout.decode("utf-8", errors="replace").strip()
        err = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            return f"[Error]\n{err}"
        return out if out else "[Success - No Output]"
    except Exception as e:
        logger.error(f"OS execution failed: {e}")
        return f"[System Error] {str(e)}"
