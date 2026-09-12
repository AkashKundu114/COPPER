import os
import platform
import shutil
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger


@tool_registry.tool(
    name="system_hardware_stats",
    description="Retrieve live local hardware telemetry including CPU utilization, memory footprint, disk usage, and host OS specs.",
    parameters={
        "type": "object",
        "properties": {},
    },
    return_description="Detailed system hardware statistics.",
    guardian_level=0,
)
async def system_hardware_stats() -> dict[str, Any]:
    try:
        # Disk usage for current drive
        total, used, free = shutil.disk_usage(".")
        disk_info = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 1),
        }

        # OS and CPU info
        host_info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_cores": os.cpu_count() or 1,
        }

        # Memory usage via psutil if available, otherwise fallback
        mem_info = {}
        try:
            import psutil

            vm = psutil.virtual_memory()
            mem_info = {
                "total_mb": round(vm.total / (1024**2), 1),
                "available_mb": round(vm.available / (1024**2), 1),
                "used_mb": round(vm.used / (1024**2), 1),
                "percent": vm.percent,
            }
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except ImportError:
            cpu_percent = None

        return {
            "status": "success",
            "host": host_info,
            "disk": disk_info,
            "memory": mem_info,
            "cpu_percent": cpu_percent,
        }
    except Exception as e:
        logger.error(f"system_hardware_stats error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="process_status",
    description="Inspect active processes on the host machine, filter by name, or find top resource-consuming tasks.",
    parameters={
        "type": "object",
        "properties": {
            "filter_name": {
                "type": "string",
                "description": "Optional substring to filter process names (e.g. 'python', 'ollama', 'node').",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of process entries to return (default: 15).",
            },
        },
    },
    return_description="List of active processes with PID, name, and memory percentage.",
    guardian_level=0,
)
async def process_status(filter_name: str | None = None, limit: int = 15) -> dict[str, Any]:
    try:
        import psutil

        procs = []
        name_filter = filter_name.lower() if filter_name else None

        for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
            try:
                p_name = p.info.get("name") or ""
                if name_filter and name_filter not in p_name.lower():
                    continue

                procs.append({
                    "pid": p.info.get("pid"),
                    "name": p_name,
                    "memory_percent": round(p.info.get("memory_percent") or 0.0, 2),
                    "cpu_percent": round(p.info.get("cpu_percent") or 0.0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory usage descending
        procs.sort(key=lambda x: x["memory_percent"], reverse=True)

        return {
            "status": "success",
            "filter": filter_name,
            "total_found": len(procs),
            "processes": procs[:limit],
        }
    except ImportError:
        return {
            "status": "warning",
            "message": "psutil library not installed for detailed process status.",
        }
    except Exception as e:
        logger.error(f"process_status error: {e}")
        return {"status": "error", "error": str(e)}
