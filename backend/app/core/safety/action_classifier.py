"""4-Tier Action Safety Classifier for C.O.P.P.E.R.

Classifies proposed agent actions into four canonical risk tiers:
  1. READ_ONLY (Level 0): Idempotent queries, status checks, reads. Always permitted.
  2. REVERSIBLE (Level 1): Non-destructive state modifications with clear undo paths.
  3. CONSEQUENTIAL (Level 2): Meaningful state, disk, or external modifications.
     Requires explicit operator confirmation ticket before execution.
  4. IRREVERSIBLE (Level 3): Permanent deletions, disk wiping, or hard safety breaches.
     Unconditionally blocked by system safety invariants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from app.core.guardian import COMPILED_SAFETY_PATTERNS, SAFETY_TRIGGERS, normalize_adversarial_text
from app.core.logger import logger


class ActionSafetyLevel(IntEnum):
    READ_ONLY = 0
    REVERSIBLE = 1
    CONSEQUENTIAL = 2
    IRREVERSIBLE = 3


@dataclass(frozen=True)
class ActionClassification:
    action_repr: str
    level: ActionSafetyLevel
    is_blocked: bool
    requires_approval: bool
    reason: str
    matched_pattern: str | None = None


# Pattern catalogs for consequential operations
CONSEQUENTIAL_PATTERNS = [
    re.compile(r"\b(git\s+push|git\s+commit|git\s+reset|git\s+checkout\s+-b)\b", re.IGNORECASE),
    re.compile(r"\b(pip\s+install|npm\s+install|cargo\s+install)\b", re.IGNORECASE),
    re.compile(r"\b(kill\s+-9|taskkill|stop-process)\b", re.IGNORECASE),
    re.compile(r"\b(write|update|modify|patch|overwrite|replace|save)\b", re.IGNORECASE),
    re.compile(r"\b(file_write|file_delete|shell_execute)\b", re.IGNORECASE),
]

READ_ONLY_TOOLS = {
    "file_read",
    "file_search",
    "directory_list",
    "system_info",
    "git_status",
    "git_log",
    "git_diff",
    "codebase_search",
    "memory_query",
    "web_search",
}

CONSEQUENTIAL_TOOLS = {
    "file_write",
    "file_delete",
    "shell_execute",
    "process_terminate",
    "calendar_delete",
    "database_migrate",
}


class ActionSafetyClassifier:
    """Evaluates proposed tool invocations and commands against the 4-tier taxonomy."""

    def classify_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ActionClassification:
        action_repr = f"{tool_name}({', '.join(f'{k}={repr(v)[:40]}' for k, v in arguments.items())})"
        norm_text = normalize_adversarial_text(action_repr)

        # 1. Check for IRREVERSIBLE (Level 3) invariants
        if any(t in norm_text for t in SAFETY_TRIGGERS) or any(p.search(norm_text) for p in COMPILED_SAFETY_PATTERNS):
            logger.warning(f"[ActionClassifier] IRREVERSIBLE action blocked: {action_repr}")
            return ActionClassification(
                action_repr=action_repr,
                level=ActionSafetyLevel.IRREVERSIBLE,
                is_blocked=True,
                requires_approval=False,
                reason="Permanent destructive command violates system invariant.",
                matched_pattern="SAFETY_INVARIANT_TRIGGER",
            )

        # 2. Check for READ_ONLY (Level 0)
        if tool_name in READ_ONLY_TOOLS and not any(p.search(norm_text) for p in CONSEQUENTIAL_PATTERNS):
            return ActionClassification(
                action_repr=action_repr,
                level=ActionSafetyLevel.READ_ONLY,
                is_blocked=False,
                requires_approval=False,
                reason="Safe idempotent read-only operation.",
            )

        # 3. Check for CONSEQUENTIAL (Level 2)
        if tool_name in CONSEQUENTIAL_TOOLS or any(p.search(norm_text) for p in CONSEQUENTIAL_PATTERNS):
            return ActionClassification(
                action_repr=action_repr,
                level=ActionSafetyLevel.CONSEQUENTIAL,
                is_blocked=False,
                requires_approval=True,
                reason="Consequential system, disk, or state modification requires operator approval ticket.",
            )

        # 4. Default to REVERSIBLE (Level 1)
        return ActionClassification(
            action_repr=action_repr,
            level=ActionSafetyLevel.REVERSIBLE,
            is_blocked=False,
            requires_approval=False,
            reason="Standard reversible state operation permitted.",
        )


action_safety_classifier = ActionSafetyClassifier()
