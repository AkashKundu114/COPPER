import asyncio
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger


async def _run_git_cmd(args: list[str], repo_path: str) -> tuple[int, str, str]:
    """Execute a git command asynchronously within the specified repo path."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace").strip(),
            stderr.decode("utf-8", errors="replace").strip(),
        )
    except Exception as e:
        return -1, "", str(e)


@tool_registry.tool(
    name="git_status",
    description="Check the working tree status, staged files, unstaged changes, and untracked files of a local Git repository.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository (default: current working directory).",
            }
        },
    },
    return_description="Git status output with current branch and modified files.",
    guardian_level=0,
)
async def git_status(repo_path: str = ".") -> dict[str, Any]:
    p = str(Path(repo_path).resolve())
    code, stdout, stderr = await _run_git_cmd(["status", "--short", "--branch"], p)
    if code != 0:
        return {"status": "error", "error": stderr or "Failed to run git status"}

    lines = stdout.splitlines()
    branch_line = lines[0] if lines else "## Unknown"
    files = lines[1:] if len(lines) > 1 else []

    return {
        "status": "success",
        "repo_path": p,
        "branch": branch_line.lstrip("# "),
        "has_changes": len(files) > 0,
        "changes": files[:50],
        "total_changes": len(files),
    }


@tool_registry.tool(
    name="git_diff",
    description="Inspect git diff changes across tracked files or against a specific commit/branch.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository.",
            },
            "staged": {
                "type": "boolean",
                "description": "Whether to inspect staged changes (--cached). Default: false.",
            },
            "file_path": {
                "type": "string",
                "description": "Specific file path to diff (optional).",
            },
        },
    },
    return_description="Unified diff text.",
    guardian_level=0,
)
async def git_diff(
    repo_path: str = ".",
    staged: bool = False,
    file_path: str | None = None,
) -> dict[str, Any]:
    p = str(Path(repo_path).resolve())
    args = ["diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.extend(["--", file_path])

    code, stdout, stderr = await _run_git_cmd(args, p)
    if code != 0:
        return {"status": "error", "error": stderr or "Failed to run git diff"}

    # Truncate large diffs to 500 lines / ~30KB to protect context
    lines = stdout.splitlines()
    truncated = False
    if len(lines) > 500:
        stdout = "\n".join(lines[:500]) + "\n... [diff truncated]"
        truncated = True

    return {
        "status": "success",
        "repo_path": p,
        "staged": staged,
        "diff": stdout,
        "truncated": truncated,
    }


@tool_registry.tool(
    name="git_log",
    description="Retrieve recent git commit history with hashes, authors, dates, and messages.",
    parameters={
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Path to the git repository.",
            },
            "max_count": {
                "type": "integer",
                "description": "Maximum number of commits to retrieve (default: 10).",
            },
        },
    },
    return_description="List of recent commits.",
    guardian_level=0,
)
async def git_log(repo_path: str = ".", max_count: int = 10) -> dict[str, Any]:
    p = str(Path(repo_path).resolve())
    fmt = "%H|%an|%ad|%s"
    code, stdout, stderr = await _run_git_cmd(
        ["log", f"-n{max_count}", f"--pretty=format:{fmt}", "--date=short"],
        p,
    )
    if code != 0:
        return {"status": "error", "error": stderr or "Failed to run git log"}

    commits = []
    for line in stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
            })

    return {
        "status": "success",
        "repo_path": p,
        "total": len(commits),
        "commits": commits,
    }
