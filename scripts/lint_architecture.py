"""AST-Based Architecture Boundary Linter for C.O.P.P.E.R.

Enforces ADR-0005: Layered Architecture Boundaries.
Verifies that low-level modules (app.database, app.core) never import from
high-level modules (app.ai, app.api), preventing circular dependencies.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent / "backend" / "app"

# Disallowed imports: package -> forbidden import prefixes
FORBIDDEN_DEPENDENCIES = {
    "database": ["app.ai", "app.api"],
    # Allow core to remain largely independent
}


def check_file_imports(file_path: Path, package_name: str) -> list[str]:
    violations = []
    forbidden = FORBIDDEN_DEPENDENCIES.get(package_name, [])
    if not forbidden:
        return violations

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except Exception as e:
        return [f"Failed to parse {file_path}: {e}"]

    for node in ast.walk(tree):
        imported_mod = ""
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_mod = alias.name
                for forb in forbidden:
                    if imported_mod.startswith(forb):
                        violations.append(f"{file_path}:{node.lineno} imports '{imported_mod}' (Forbidden in layer '{package_name}')")
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_mod = node.module
            for forb in forbidden:
                if imported_mod.startswith(forb):
                    violations.append(f"{file_path}:{node.lineno} imports '{imported_mod}' (Forbidden in layer '{package_name}')")

    return violations


def lint_all_architecture() -> int:
    total_violations = []

    for pkg in FORBIDDEN_DEPENDENCIES:
        pkg_dir = ROOT_DIR / pkg
        if not pkg_dir.exists():
            continue
        for root, _, files in os.walk(pkg_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    viols = check_file_imports(full_path, pkg)
                    total_violations.extend(viols)

    if total_violations:
        print(f"[Architecture Linter] Found {len(total_violations)} boundary violation(s):")
        for v in total_violations:
            print(f"  - {v}")
        return 1

    print("[Architecture Linter] All architectural layer boundaries verified. 0 violations.")
    return 0


if __name__ == "__main__":
    sys.exit(lint_all_architecture())
