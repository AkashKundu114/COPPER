import os
import subprocess
import platform
from typing import Optional
from app.core.logger import logger

OS = platform.system()  # Windows | Linux | Darwin


async def get_system_info() -> dict:
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "os": OS,
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / 1e9, 2),
            "memory_used_gb": round(memory.used / 1e9, 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / 1e9, 2),
            "disk_used_gb": round(disk.used / 1e9, 2),
            "disk_percent": disk.percent,
        }
    except ImportError:
        return {"os": OS, "cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}


async def run_command(command: str, shell: bool = True) -> dict:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Command timed out", "returncode": -1, "success": False}
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}


async def get_running_processes() -> list[dict]:
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(processes, key=lambda x: x.get("cpu_percent", 0), reverse=True)[:20]
    except Exception:
        return []


async def kill_process(pid: int) -> bool:
    try:
        import psutil
        proc = psutil.Process(pid)
        proc.terminate()
        return True
    except Exception as e:
        logger.error(f"Kill process error: {e}")
        return False


async def set_volume(level: int) -> bool:
    """Set system volume (0-100)."""
    level = max(0, min(100, level))
    try:
        if OS == "Windows":
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        elif OS == "Linux":
            await run_command(f"amixer sset Master {level}%")
        elif OS == "Darwin":
            await run_command(f"osascript -e 'set volume output volume {level}'")
        return True
    except Exception as e:
        logger.error(f"Set volume error: {e}")
        return False
