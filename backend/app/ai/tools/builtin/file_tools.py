import fnmatch
import os
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger


@tool_registry.tool(
    name="file_read",
    description="Read the contents of a local file as text. Safe and read-only.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative file path to read."},
            "encoding": {"type": "string", "description": "Text encoding (defaults to 'utf-8')."},
        },
        "required": ["path"],
    },
    return_description="String containing file contents or error message if unreadable.",
    guardian_level=0,
)
async def file_read(path: str, encoding: str = "utf-8") -> dict[str, Any]:
    try:
        p = Path(path).resolve()
        if not p.exists():
            return {"status": "error", "error": f"File does not exist: {path}"}
        if not p.is_file():
            return {"status": "error", "error": f"Path is not a regular file: {path}"}

        # Size check limit: 5MB
        size = p.stat().st_size
        if size > 5 * 1024 * 1024:
            return {"status": "error", "error": f"File is too large ({size} bytes > 5MB limit)."}

        with open(p, encoding=encoding, errors="replace") as f:
            content = f.read()

        return {
            "status": "success",
            "path": str(p),
            "size_bytes": size,
            "content": content,
        }
    except Exception as e:
        logger.error(f"file_read error for '{path}': {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="file_write",
    description="Write or overwrite contents of a file on the local filesystem. Modifies disk state.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path to write to."},
            "content": {"type": "string", "description": "Text content to write into the file."},
            "mode": {
                "type": "string",
                "description": "Write mode: 'overwrite' (default) or 'append'.",
            },
        },
        "required": ["path", "content"],
    },
    return_description="Status confirmation and bytes written.",
    guardian_level=2,  # CHALLENGE
)
async def file_write(path: str, content: str, mode: str = "overwrite") -> dict[str, Any]:
    try:
        p = Path(path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)

        write_mode = "a" if mode.lower() == "append" else "w"
        with open(p, write_mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "path": str(p),
            "mode": mode,
            "bytes_written": len(content.encode("utf-8")),
            "message": f"Successfully wrote to {p.name}",
        }
    except Exception as e:
        logger.error(f"file_write error for '{path}': {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="file_list",
    description="List files and directories within a given local directory path matching a pattern.",
    parameters={
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Target directory path to inspect (defaults to '.')."},
            "pattern": {"type": "string", "description": "Glob match pattern, e.g. '*.py' or '*' (defaults to '*')."},
        },
        "required": [],
    },
    return_description="List of filenames, types, and sizes.",
    guardian_level=0,
)
async def file_list(directory: str = ".", pattern: str = "*") -> dict[str, Any]:
    try:
        target_dir = Path(directory).resolve()
        if not target_dir.exists():
            return {"status": "error", "error": f"Directory does not exist: {directory}"}
        if not target_dir.is_dir():
            return {"status": "error", "error": f"Path is not a directory: {directory}"}

        entries = []
        for item in os.listdir(target_dir):
            if fnmatch.fnmatch(item, pattern):
                full = target_dir / item
                is_dir = full.is_dir()
                size = 0 if is_dir else (full.stat().st_size if full.exists() else 0)
                entries.append(
                    {
                        "name": item,
                        "is_dir": is_dir,
                        "size_bytes": size,
                        "path": str(full),
                    }
                )

        return {
            "status": "success",
            "directory": str(target_dir),
            "total_matches": len(entries),
            "entries": entries[:100],  # cap at 100 entries for context safety
        }
    except Exception as e:
        logger.error(f"file_list error for '{directory}': {e}")
        return {"status": "error", "error": str(e)}
