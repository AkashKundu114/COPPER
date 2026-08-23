import asyncio

from app.core.logger import logger


async def execute_powershell(command: str, timeout: int = 30) -> str:
    """Executes a PowerShell command directly on the host OS."""
    try:
        process = await asyncio.create_subprocess_exec(
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
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
