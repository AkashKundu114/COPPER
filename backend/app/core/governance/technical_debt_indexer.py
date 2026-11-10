"""AST Cyclomatic Complexity and Architectural Code Rot Indexer.

Implements Stage 8 Maintainability & Evolvability Architecture:
- Parses Python source files via AST to calculate function cyclomatic complexity.
- Tracks TODO/FIXME technical debt annotations, large function bodies, and parameter counts.
- Computes a normalized Architectural Health Index (0.0 to 1.0) and flags maintenance hotspots.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class FunctionComplexityMetric:
    name: str
    line_number: int
    cyclomatic_complexity: int
    lines_of_code: int
    parameter_count: int
    is_excessive: bool


@dataclass
class FileDebtAnalysis:
    file_path: str
    total_loc: int
    function_count: int
    average_complexity: float
    max_complexity: int
    todo_count: int
    complex_functions: list[FunctionComplexityMetric] = field(default_factory=list)


@dataclass
class CodebaseHealthIndexReport:
    scanned_files_count: int
    total_loc: int
    overall_health_score: float  # 0.0 (decayed) to 1.0 (pristine)
    high_complexity_hotspots: list[FunctionComplexityMetric]
    total_debt_annotations: int


class TechnicalDebtIndexer:
    """AST-driven code analysis engine for identifying architectural debt and complexity hotspots."""

    MAX_SAFE_COMPLEXITY = 10
    MAX_SAFE_PARAMS = 7

    def analyze_source_code(self, source_code: str, file_path: str = "<memory>") -> FileDebtAnalysis:
        """Parse source code string via AST and calculate complexity metrics."""
        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError:
            return FileDebtAnalysis(
                file_path=file_path,
                total_loc=len(source_code.splitlines()),
                function_count=0,
                average_complexity=0.0,
                max_complexity=0,
                todo_count=0,
            )

        lines = source_code.splitlines()
        loc = len(lines)
        todo_count = sum(1 for line in lines if "TODO" in line or "FIXME" in line)

        func_metrics: list[FunctionComplexityMetric] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1

                func_loc = (node.end_lineno or node.lineno) - node.lineno + 1
                param_count = len(node.args.args)
                is_excessive = complexity > self.MAX_SAFE_COMPLEXITY or param_count > self.MAX_SAFE_PARAMS

                metric = FunctionComplexityMetric(
                    name=node.name,
                    line_number=node.lineno,
                    cyclomatic_complexity=complexity,
                    lines_of_code=func_loc,
                    parameter_count=param_count,
                    is_excessive=is_excessive,
                )
                func_metrics.append(metric)

        avg_comp = sum(m.cyclomatic_complexity for m in func_metrics) / len(func_metrics) if func_metrics else 1.0
        max_comp = max((m.cyclomatic_complexity for m in func_metrics), default=1)
        excessive_funcs = [m for m in func_metrics if m.is_excessive]

        return FileDebtAnalysis(
            file_path=file_path,
            total_loc=loc,
            function_count=len(func_metrics),
            average_complexity=round(avg_comp, 2),
            max_complexity=max_comp,
            todo_count=todo_count,
            complex_functions=excessive_funcs,
        )

    def compute_health_report(self, analyses: list[FileDebtAnalysis]) -> CodebaseHealthIndexReport:
        """Aggregate file debt metrics into a unified codebase health index."""
        if not analyses:
            return CodebaseHealthIndexReport(0, 0, 1.0, [], 0)

        total_files = len(analyses)
        total_loc = sum(a.total_loc for a in analyses)
        total_todos = sum(a.todo_count for a in analyses)
        hotspots: list[FunctionComplexityMetric] = []

        for a in analyses:
            hotspots.extend(a.complex_functions)

        # Health penalty calculation
        # Baseline score: 1.0
        # Hotspot penalty: -0.05 per excessive function (max -0.4)
        # Todo penalty: -0.01 per TODO (max -0.2)
        hotspot_penalty = min(0.40, len(hotspots) * 0.05)
        todo_penalty = min(0.20, total_todos * 0.01)
        health_score = max(0.0, 1.0 - hotspot_penalty - todo_penalty)

        return CodebaseHealthIndexReport(
            scanned_files_count=total_files,
            total_loc=total_loc,
            overall_health_score=round(health_score, 2),
            high_complexity_hotspots=hotspots,
            total_debt_annotations=total_todos,
        )
