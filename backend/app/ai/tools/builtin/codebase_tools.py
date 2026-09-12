import ast
import os
import re
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    "env",
    "target",
}

SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".toml", ".yaml", ".yml"}


def _parse_python_file(path: Path) -> dict[str, Any]:
    """Parse a Python source file using AST to extract functions, classes, and imports."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except Exception as e:
        return {"error": f"Failed to parse AST: {e}"}

    classes = []
    functions = []
    imports = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                m.name
                for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            doc = ast.get_docstring(node)
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": methods,
                "doc": doc.strip() if doc else None,
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            doc = ast.get_docstring(node)
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "args": args,
                "doc": doc.strip() if doc else None,
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(f"{mod}: {', '.join(names)}")

    return {
        "classes": classes,
        "functions": functions,
        "imports": imports[:25],
        "total_lines": len(source.splitlines()),
    }


def _parse_javascript_file(path: Path) -> dict[str, Any]:
    """Extract functions, classes, and exports from JS/TS using regex."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    lines = source.splitlines()
    classes = []
    functions = []

    class_pattern = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)")
    func_pattern = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)")
    const_func_pattern = re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>")

    for i, line in enumerate(lines, start=1):
        c_match = class_pattern.search(line)
        if c_match:
            classes.append({"name": c_match.group(1), "line": i})
            continue

        f_match = func_pattern.search(line)
        if f_match:
            functions.append({
                "name": f_match.group(1),
                "line": i,
                "args": [a.strip() for a in f_match.group(2).split(",") if a.strip()],
            })
            continue

        cf_match = const_func_pattern.search(line)
        if cf_match:
            functions.append({
                "name": cf_match.group(1),
                "line": i,
                "args": [a.strip() for a in cf_match.group(2).split(",") if a.strip()],
            })

    return {
        "classes": classes,
        "functions": functions,
        "total_lines": len(lines),
    }


@tool_registry.tool(
    name="codebase_map",
    description="Generate a high-level architectural and symbol map of a project directory without reading entire files.",
    parameters={
        "type": "object",
        "properties": {
            "root_path": {
                "type": "string",
                "description": "Root directory path to map (defaults to current working directory).",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory traversal depth (default: 3).",
            },
            "include_symbols": {
                "type": "boolean",
                "description": "Whether to parse classes and functions using AST (default: true).",
            },
        },
    },
    return_description="Hierarchical map of modules, classes, and exported symbols.",
    guardian_level=0,
)
async def codebase_map(
    root_path: str = ".",
    max_depth: int = 3,
    include_symbols: bool = True,
) -> dict[str, Any]:
    try:
        base = Path(root_path).resolve()
        if not base.exists() or not base.is_dir():
            return {"status": "error", "error": f"Invalid directory path: {root_path}"}

        file_tree = {}
        total_files = 0
        total_symbols = 0

        for current_root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            rel_root = Path(current_root).relative_to(base)
            depth = len(rel_root.parts)
            if depth >= max_depth:
                dirs.clear()
                continue

            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue

                full_path = Path(current_root) / f
                rel_file_str = str(full_path.relative_to(base)).replace("\\", "/")
                total_files += 1

                file_info: dict[str, Any] = {
                    "size_bytes": full_path.stat().st_size,
                }

                if include_symbols:
                    if ext == ".py":
                        parsed = _parse_python_file(full_path)
                        file_info.update(parsed)
                        total_symbols += len(parsed.get("classes", [])) + len(parsed.get("functions", []))
                    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                        parsed = _parse_javascript_file(full_path)
                        file_info.update(parsed)
                        total_symbols += len(parsed.get("classes", [])) + len(parsed.get("functions", []))

                file_tree[rel_file_str] = file_info

                if total_files > 250:
                    break
            if total_files > 250:
                break

        return {
            "status": "success",
            "root_path": str(base),
            "total_files_scanned": total_files,
            "total_symbols_indexed": total_symbols,
            "tree": file_tree,
        }
    except Exception as e:
        logger.error(f"codebase_map error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="codebase_symbol_lookup",
    description="Locate definitions and references for a specific class, function, or symbol across the codebase.",
    parameters={
        "type": "object",
        "properties": {
            "symbol_name": {
                "type": "string",
                "description": "Name of the class, function, or variable to locate.",
            },
            "root_path": {
                "type": "string",
                "description": "Root directory path to search (defaults to current working directory).",
            },
        },
        "required": ["symbol_name"],
    },
    return_description="List of occurrences, definition line numbers, arguments, and docstrings.",
    guardian_level=0,
)
async def codebase_symbol_lookup(
    symbol_name: str,
    root_path: str = ".",
) -> dict[str, Any]:
    try:
        base = Path(root_path).resolve()
        if not base.exists() or not base.is_dir():
            return {"status": "error", "error": f"Invalid directory: {root_path}"}

        matches = []
        symbol_lower = symbol_name.lower()

        for current_root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for f in files:
                p = Path(current_root) / f
                if p.suffix == ".py":
                    parsed = _parse_python_file(p)
                    for c in parsed.get("classes", []):
                        if symbol_lower in c["name"].lower():
                            matches.append({
                                "type": "class",
                                "name": c["name"],
                                "file": str(p.relative_to(base)).replace("\\", "/"),
                                "line": c["line"],
                                "methods": c.get("methods", []),
                                "doc": c.get("doc"),
                            })
                    for fn in parsed.get("functions", []):
                        if symbol_lower in fn["name"].lower():
                            matches.append({
                                "type": "function",
                                "name": fn["name"],
                                "file": str(p.relative_to(base)).replace("\\", "/"),
                                "line": fn["line"],
                                "args": fn.get("args", []),
                                "is_async": fn.get("is_async", False),
                                "doc": fn.get("doc"),
                            })
                elif p.suffix in {".js", ".jsx", ".ts", ".tsx"}:
                    parsed = _parse_javascript_file(p)
                    for c in parsed.get("classes", []):
                        if symbol_lower in c["name"].lower():
                            matches.append({
                                "type": "class",
                                "name": c["name"],
                                "file": str(p.relative_to(base)).replace("\\", "/"),
                                "line": c["line"],
                            })
                    for fn in parsed.get("functions", []):
                        if symbol_lower in fn["name"].lower():
                            matches.append({
                                "type": "function",
                                "name": fn["name"],
                                "file": str(p.relative_to(base)).replace("\\", "/"),
                                "line": fn["line"],
                                "args": fn.get("args", []),
                            })

        return {
            "status": "success",
            "symbol": symbol_name,
            "total_matches": len(matches),
            "matches": matches,
        }
    except Exception as e:
        logger.error(f"codebase_symbol_lookup error: {e}")
        return {"status": "error", "error": str(e)}
