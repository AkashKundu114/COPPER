"""Abstract Syntax Tree (AST) Security Validator for COPPER Sandbox.

Performs static analysis of Python source code prior to execution to enforce
strict isolation boundaries, intercepting arbitrary code execution, unauthorized
imports, sensitive dunder reflection, destructive filesystem operations, and
unauthorized network calls before processes are spawned.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ASTViolation:
    """Represents a specific security violation detected during AST traversal."""

    node_type: str
    line_number: int
    description: str
    severity: str  # "warning" | "critical"


@dataclass
class ASTValidationResult:
    """Structured result returned by the AST security validator."""

    is_safe: bool
    violations: list[ASTViolation] = field(default_factory=list)
    risk_level: str = "safe"  # "safe" | "suspicious" | "dangerous" | "blocked"


# Modules strictly disallowed from being imported in the sandbox
FORBIDDEN_MODULES: frozenset[str] = frozenset({
    "os",
    "subprocess",
    "shutil",
    "sys",
    "socket",
    "ctypes",
    "importlib",
    "__builtin__",
    "builtins",
    "signal",
    "multiprocessing",
    "threading",
    "pty",
    "commands",
    "posix",
    "nt",
    "asyncio.subprocess",
    # Network libraries
    "urllib",
    "urllib3",
    "requests",
    "http",
    "httpx",
    "aiohttp",
    "ftplib",
    "telnetlib",
    "smtplib",
    "xmlrpc",
})

# Root function calls strictly forbidden (code execution / reflection escapes)
FORBIDDEN_CALLS: frozenset[str] = frozenset({
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
})

# Calls flagged as suspicious (warnings)
SUSPICIOUS_CALLS: frozenset[str] = frozenset({
    "locals",
    "vars",
})

# Dunder attributes used in sandbox escape exploits and metaclass hijacking
FORBIDDEN_DUNDERS: frozenset[str] = frozenset({
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__code__",
    "__bases__",
    "__mro__",
})

# Pathlib / file system modification and deletion methods
PATH_WRITE_METHODS: frozenset[str] = frozenset({
    "unlink",
    "rmdir",
    "write_text",
    "write_bytes",
    "mkdir",
    "rename",
    "replace",
    "touch",
    "chmod",
    "lchmod",
    "symlink_to",
    "hardlink_to",
})

# Modes in open() that permit writing, appending, or mutating files
WRITE_MODES: frozenset[str] = frozenset({"w", "a", "x", "+"})


class ASTSecurityVisitor(ast.NodeVisitor):
    """AST NodeVisitor that walks the syntax tree and detects dangerous constructs."""

    def __init__(self) -> None:
        super().__init__()
        self.violations: list[ASTViolation] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Inspects direct import statements (e.g., import os, import socket)."""
        for alias in node.names:
            root_module = alias.name.split(".")[0]
            if root_module in FORBIDDEN_MODULES or alias.name in FORBIDDEN_MODULES:
                self.violations.append(
                    ASTViolation(
                        node_type="Import",
                        line_number=node.lineno,
                        description=f"Import of forbidden module '{alias.name}' is blocked.",
                        severity="critical",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Inspects from ... import statements (e.g., from subprocess import Popen)."""
        if node.module:
            root_module = node.module.split(".")[0]
            if root_module in FORBIDDEN_MODULES or node.module in FORBIDDEN_MODULES:
                self.violations.append(
                    ASTViolation(
                        node_type="ImportFrom",
                        line_number=node.lineno,
                        description=f"Import from forbidden module '{node.module}' is blocked.",
                        severity="critical",
                    )
                )
        for alias in node.names:
            if alias.name in FORBIDDEN_CALLS or alias.name in FORBIDDEN_MODULES:
                self.violations.append(
                    ASTViolation(
                        node_type="ImportFrom",
                        line_number=node.lineno,
                        description=f"Import of sensitive entity '{alias.name}' is blocked.",
                        severity="critical",
                    )
                )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Inspects attribute lookups for forbidden dunders (e.g., obj.__subclasses__)."""
        if node.attr in FORBIDDEN_DUNDERS:
            self.violations.append(
                ASTViolation(
                    node_type="Attribute",
                    line_number=node.lineno,
                    description=f"Access to forbidden dunder attribute '{node.attr}' is blocked.",
                    severity="critical",
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Inspects function and method invocations for dangerous operations."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_CALLS:
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description=f"Call to forbidden function '{func_name}()' is blocked.",
                        severity="critical",
                    )
                )
            elif func_name in SUSPICIOUS_CALLS:
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description=f"Call to '{func_name}()' is flagged as suspicious.",
                        severity="warning",
                    )
                )
            elif func_name == "open":
                self._check_open_call(node)
            elif func_name in ("getattr", "setattr", "delattr"):
                self._check_attr_builtins(node, func_name)

        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            # ast.literal_eval is explicitly allowed and safe
            if attr_name == "literal_eval":
                pass
            elif attr_name in FORBIDDEN_CALLS:
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description=f"Call to forbidden method '{attr_name}()' is blocked.",
                        severity="critical",
                    )
                )
            elif attr_name in PATH_WRITE_METHODS:
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description=f"Destructive file system operation '{attr_name}()' is blocked.",
                        severity="critical",
                    )
                )
            elif attr_name in ("connect", "send", "sendall", "recv", "listen", "bind", "urlopen"):
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description=f"Direct network call '{attr_name}()' is blocked.",
                        severity="critical",
                    )
                )

        self.generic_visit(node)

    def _check_open_call(self, node: ast.Call) -> None:
        """Inspects open() calls to detect write, append, or mutating modes."""
        mode_arg = None
        if len(node.args) >= 2:
            mode_arg = node.args[1]
        else:
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode_arg = kw.value
                    break

        if mode_arg is not None:
            if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                mode_str = mode_arg.value.lower()
                if any(char in mode_str for char in WRITE_MODES):
                    self.violations.append(
                        ASTViolation(
                            node_type="Call",
                            line_number=node.lineno,
                            description=f"Call to open() with write/append mode '{mode_str}' is blocked.",
                            severity="critical",
                        )
                    )
            else:
                # Dynamic mode expression cannot be statically proven safe
                self.violations.append(
                    ASTViolation(
                        node_type="Call",
                        line_number=node.lineno,
                        description="Call to open() with dynamic or non-literal mode is blocked.",
                        severity="critical",
                    )
                )

    def _check_attr_builtins(self, node: ast.Call, builtin_name: str) -> None:
        """Checks getattr, setattr, delattr against forbidden attributes and primitives."""
        if len(node.args) >= 2:
            attr_arg = node.args[1]
            if isinstance(attr_arg, ast.Constant) and isinstance(attr_arg.value, str):
                target_attr = attr_arg.value
                if (
                    target_attr in FORBIDDEN_DUNDERS
                    or target_attr in FORBIDDEN_CALLS
                    or target_attr in ("system", "popen", "spawn")
                ):
                    self.violations.append(
                        ASTViolation(
                            node_type="Call",
                            line_number=node.lineno,
                            description=(
                                f"Call to {builtin_name}() accessing sensitive attribute "
                                f"'{target_attr}' is blocked."
                            ),
                            severity="critical",
                        )
                    )


class ASTSecurityValidator:
    """Validates Python code by parsing and inspecting its Abstract Syntax Tree (AST)."""

    def validate(self, code: str) -> ASTValidationResult:
        """Parses and validates Python code, returning a structured ASTValidationResult."""
        if not code or not code.strip():
            return ASTValidationResult(is_safe=True, violations=[], risk_level="safe")

        try:
            tree = ast.parse(code)
        except SyntaxError as err:
            violation = ASTViolation(
                node_type="SyntaxError",
                line_number=err.lineno or 1,
                description=f"Python SyntaxError: {err.msg}",
                severity="critical",
            )
            return ASTValidationResult(
                is_safe=False,
                violations=[violation],
                risk_level="blocked",
            )

        visitor = ASTSecurityVisitor()
        visitor.visit(tree)

        violations = visitor.violations
        if not violations:
            return ASTValidationResult(is_safe=True, violations=[], risk_level="safe")

        has_critical = any(v.severity == "critical" for v in violations)
        has_warning = any(v.severity == "warning" for v in violations)

        if has_critical:
            dangerous_keywords = ("open() with write", "Destructive file system", "Direct network call")
            is_dangerous = any(any(kw in v.description for kw in dangerous_keywords) for v in violations)
            has_blocked_keywords = (
                "forbidden module",
                "forbidden function",
                "forbidden dunder",
                "getattr()",
                "Syntax error",
            )
            is_blocked = any(any(kw in v.description for kw in has_blocked_keywords) for v in violations)

            risk_level = "blocked" if (is_blocked or not is_dangerous) else "dangerous"
            return ASTValidationResult(
                is_safe=False,
                violations=violations,
                risk_level=risk_level,
            )

        if has_warning:
            return ASTValidationResult(
                is_safe=False,
                violations=violations,
                risk_level="suspicious",
            )

        return ASTValidationResult(is_safe=True, violations=[], risk_level="safe")


# Default global instance
ast_security_validator = ASTSecurityValidator()
