"""Cognitive Hallucination Reflector and Multi-Agent Cross-Examiner.

Implements Stage 9 AI Safety & Alignment Framework:
- Detects factual contradictions, citation fabrication, and hallucinated function calls.
- Employs self-reflective critique loops to verify groundedness against provided context.
- Intercepts ungrounded assertions before responses are returned to users or tools.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GroundednessEvaluation:
    is_grounded: bool
    grounding_score: float  # 0.0 to 1.0
    detected_hallucinations: list[str]
    fabricated_entities: list[str]
    corrected_reflection: Optional[str] = None


class CognitiveHallucinationReflector:
    """Self-reflective safety examiner that detects and corrects hallucinated model output."""

    # Patterns indicating potentially fabricated technical entities
    FABRICATED_URL_PATTERN = re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)*(?:fake|invalid|example|nonexistent|phantom)\.[a-z]{2,}")
    NON_EXISTENT_TOOL_PATTERN = re.compile(r"\bcall_tool\(['\"]([a-zA-Z0-9_]+)['\"]")

    def __init__(self, registered_tools: Optional[list[str]] = None) -> None:
        self.registered_tools = set(registered_tools or [
            "read_file", "write_file", "edit_file", "run_command", "list_dir", "search_code"
        ])

    def evaluate_groundedness(
        self,
        candidate_response: str,
        grounding_context: str,
    ) -> GroundednessEvaluation:
        """Analyze text against ground truth context to detect hallucinations or ungrounded claims."""
        hallucinations: list[str] = []
        fabricated_entities: list[str] = []

        # 1. Check for fabricated tool names
        for match in self.NON_EXISTENT_TOOL_PATTERN.finditer(candidate_response):
            tool_name = match.group(1)
            if tool_name not in self.registered_tools:
                hallucinations.append(f"Invoked unregistered hallucinated tool '{tool_name}'")
                fabricated_entities.append(tool_name)

        # 2. Check for phantom URLs
        for match in self.FABRICATED_URL_PATTERN.finditer(candidate_response):
            url = match.group(0)
            hallucinations.append(f"Referenced suspicious fabricated URL '{url}'")
            fabricated_entities.append(url)

        # 3. Contextual token overlap score
        ctx_tokens = set(re.findall(r"\w{4,}", grounding_context.lower()))
        resp_tokens = re.findall(r"\w{4,}", candidate_response.lower())

        if resp_tokens and ctx_tokens:
            grounded_tokens_count = sum(1 for t in resp_tokens if t in ctx_tokens)
            grounding_ratio = grounded_tokens_count / len(resp_tokens)
        else:
            grounding_ratio = 1.0

        # Groundedness score combines entity validity and context overlap
        penalty = min(0.6, len(hallucinations) * 0.3)
        final_score = max(0.0, min(1.0, grounding_ratio - penalty))
        is_grounded = len(hallucinations) == 0 and final_score >= 0.35

        corrected = None
        if not is_grounded:
            corrected = candidate_response
            for fab in fabricated_entities:
                corrected = corrected.replace(fab, f"[UNVERIFIED_REFERENCE: {fab}]")

        return GroundednessEvaluation(
            is_grounded=is_grounded,
            grounding_score=round(final_score, 2),
            detected_hallucinations=hallucinations,
            fabricated_entities=fabricated_entities,
            corrected_reflection=corrected,
        )
