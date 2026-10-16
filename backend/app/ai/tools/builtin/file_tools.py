import fnmatch
import os
import tempfile
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.config import settings
from app.core.logger import logger

RESTRICTED_FILENAMES = {".env", ".git", "id_rsa", "id_ed25519", "known_hosts"}
RESTRICTED_SYSTEM_DIRS = [
    Path(os.environ.get("WINDIR", "C:\\Windows")).resolve(),
    Path(os.environ.get("ProgramFiles", "C:\\Program Files")).resolve(),
    Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")).resolve(),
    Path("/etc").resolve(),
    Path("/sys").resolve(),
    Path("/proc").resolve(),
    Path("/root").resolve(),
]


def _get_allowed_roots() -> list[Path]:
    roots = [
        Path(settings.DOCUMENTS_DIR).resolve(),
        Path(__file__).resolve().parents[5],
        Path(tempfile.gettempdir()).resolve(),
    ]
    return [r for r in roots if r.exists()]


def validate_safe_path(target_path: str | Path, allow_nonexistent: bool = False) -> tuple[bool, Path | None, str | None]:
    """Validates that target_path is confined to permitted directory roots (project workspace,"""
    try:
        resolved = Path(target_path).resolve()

        if resolved.name.startswith(".env") or resolved.name.lower() in RESTRICTED_FILENAMES:
            return False, None, f"Access denied: access to sensitive credential/configuration file '{resolved.name}' is prohibited."

        for part in resolved.parts:
            if part.lower() in {".ssh", ".aws", ".azure", ".gnupg"}:
                return False, None, f"Access denied: directory '{part}' contains sensitive credentials."

        for sys_dir in RESTRICTED_SYSTEM_DIRS:
            if str(sys_dir).strip() and (resolved == sys_dir or sys_dir in resolved.parents):
                return False, None, f"Access denied: path '{target_path}' is inside protected system directory '{sys_dir}'."

        allowed_roots = _get_allowed_roots()
        is_allowed = any(resolved == root or root in resolved.parents for root in allowed_roots)
        if not is_allowed:
            return False, None, f"Access denied: path '{target_path}' is outside permitted workspace and document boundaries."

        return True, resolved, None
    except Exception as e:
        return False, None, f"Invalid path validation: {e}"


@tool_registry.tool(
    name="file_read",
    description="Read the contents of a local file as text. Safe and read-only within permitted workspace boundaries.",
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
        is_safe, p, err = validate_safe_path(path)
        if not is_safe or p is None:
            return {"status": "error", "error": err or f"Access denied for path: {path}"}

        if not p.exists():
            return {"status": "error", "error": f"File does not exist: {path}"}
        if not p.is_file():
            return {"status": "error", "error": f"Path is not a regular file: {path}"}

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
    guardian_level=2,
)
async def file_write(path: str, content: str, mode: str = "overwrite") -> dict[str, Any]:
    try:
        is_safe, p, err = validate_safe_path(path, allow_nonexistent=True)
        if not is_safe or p is None:
            return {"status": "error", "error": err or f"Access denied for path: {path}"}

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
        is_safe, target_dir, err = validate_safe_path(directory)
        if not is_safe or target_dir is None:
            return {"status": "error", "error": err or f"Access denied for directory: {directory}"}

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
            "entries": entries[:100],
        }
    except Exception as e:
        logger.error(f"file_list error for '{directory}': {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="file_search",
    description="Search for files by content (grep-style) and/or filename pattern recursively.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Text to search for in file contents."},
            "directory": {"type": "string", "description": "Root directory to search in (defaults to '.')."},
            "pattern": {
                "type": "string",
                "description": "Glob pattern to filter filenames, e.g. '*.py' (defaults to '*').",
            },
            "max_results": {"type": "integer", "description": "Maximum matches to return (defaults to 20)."},
            "case_sensitive": {
                "type": "boolean",
                "description": "Whether search is case-sensitive (defaults to false).",
            },
        },
        "required": ["query"],
    },
    return_description="List of matches with file path, line number, line content, and context.",
    guardian_level=0,
)
async def file_search(
    query: str,
    directory: str = ".",
    pattern: str = "*",
    max_results: int = 20,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    try:
        is_safe, target_dir, err = validate_safe_path(directory)
        if not is_safe or target_dir is None:
            return {"status": "error", "error": err or f"Access denied for directory: {directory}"}

        if not target_dir.exists():
            return {"status": "error", "error": f"Directory does not exist: {directory}"}
        if not target_dir.is_dir():
            return {"status": "error", "error": f"Path is not a directory: {directory}"}

        search_query = query if case_sensitive else query.lower()
        matches = []

        for p in target_dir.rglob(pattern):
            if not p.is_file():
                continue

            try:
                rel_path = p.relative_to(target_dir)
                if len(rel_path.parts) > 10:
                    continue

                size = p.stat().st_size
                if size > 2 * 1024 * 1024:
                    continue

                with open(p, "rb") as f:
                    chunk = f.read(1024)
                    if b"\x00" in chunk:
                        continue

                with open(p, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                for i, line in enumerate(lines):
                    line_to_check = line if case_sensitive else line.lower()
                    if search_query in line_to_check:
                        context_above = lines[i - 1].strip() if i > 0 else None
                        context_below = lines[i + 1].strip() if i < len(lines) - 1 else None

                        matches.append(
                            {
                                "path": str(p),
                                "line_number": i + 1,
                                "line_content": line.strip(),
                                "context_above": context_above,
                                "context_below": context_below,
                            }
                        )

                        if len(matches) >= max_results:
                            break

            except Exception:
                continue

            if len(matches) >= max_results:
                break

        return {
            "status": "success",
            "directory": str(target_dir),
            "total_matches": len(matches),
            "matches": matches,
        }
    except Exception as e:
        logger.error(f"file_search error for '{directory}': {e}")
        return {"status": "error", "error": str(e)}
