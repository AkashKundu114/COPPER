"""
Guardian disagreement engine.
Master System Prompt §4 (Guardian Mode) and §5 (Disagreement Protocol).

This module NEVER blocks user autonomy on its own — it classifies a proposed
action and returns a structured verdict. The caller (chat_service / agent_router)
decides how to surface it (execute silently, suggest, challenge, or require
explicit confirmation for a safety boundary).
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
from app.core.logger import logger


class DisagreementLevel(IntEnum):
    EXECUTE = 0    # no meaningful concern — just do it
    SUGGEST = 1    # minor optimization opportunity, non-blocking
    CHALLENGE = 2  # strong evidence the action conflicts with a goal/commitment
    SAFETY = 3     # hard boundary — explicit confirmation required


@dataclass
class GuardianVerdict:
    level: DisagreementLevel
    reasoning: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    confidence: Optional[str] = None  # "high" | "medium" | "low"
    recommendation: Optional[str] = None
    requires_confirmation: bool = False

    def to_dict(self) -> dict:
        return {
            "level": int(self.level),
            "level_name": self.level.name,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "requires_confirmation": self.requires_confirmation,
        }


# Keyword-level safety boundary triggers (Level 3). Mirrors the existing
# command blocklist in automation.py — kept in sync, not duplicated logic.
SAFETY_TRIGGERS = [
    "rm -rf", "format ", "del /f", "dd if=", "mkfs",
    "delete all", "wipe", "factory reset",
]


class GuardianEngine:
    """
    Evaluates a proposed action against known goals/commitments/evidence and
    returns a DisagreementLevel + supporting rationale. Evidence gathering
    (querying UserMemoryV2, calendar, task deadlines) is injected by the
    caller via `context` rather than fetched here, so this stays testable
    and framework-agnostic.
    """

    def evaluate(
        self,
        proposed_action: str,
        context: dict,
    ) -> GuardianVerdict:
        """
        context is expected to optionally contain:
          - conflicting_commitments: list[str]
          - relevant_memories: list[dict]  (UserMemoryV2.to_dict())
          - reversible: bool
          - is_destructive: bool
        """
        action_lower = proposed_action.lower()

        # Level 3 — hard safety boundary
        if context.get("is_destructive") or any(t in action_lower for t in SAFETY_TRIGGERS):
            return GuardianVerdict(
                level=DisagreementLevel.SAFETY,
                reasoning="This action is destructive or irreversible.",
                requires_confirmation=True,
                recommendation="Confirm explicitly before I proceed, or choose a safer alternative.",
            )

        conflicts = context.get("conflicting_commitments") or []
        if conflicts:
            return GuardianVerdict(
                level=DisagreementLevel.CHALLENGE,
                reasoning="This conflicts with an existing commitment or goal.",
                evidence=conflicts,
                confidence=context.get("confidence", "medium"),
                recommendation=context.get("recommendation"),
            )

        suggestion = context.get("optimization_suggestion")
        if suggestion:
            return GuardianVerdict(
                level=DisagreementLevel.SUGGEST,
                reasoning=suggestion,
                confidence=context.get("confidence", "medium"),
            )

        return GuardianVerdict(level=DisagreementLevel.EXECUTE)

    def format_challenge(self, verdict: GuardianVerdict) -> str:
        """Render a Level 2/3 verdict per the Disagreement Protocol (§5) wording."""
        if verdict.level < DisagreementLevel.CHALLENGE:
            return verdict.reasoning or ""
        lines = [f"I disagree with this because {verdict.reasoning}"]
        if verdict.evidence:
            lines.append("My evidence is:")
            lines.extend(f"  - {e}" for e in verdict.evidence)
        if verdict.confidence:
            lines.append(f"My confidence is {verdict.confidence}.")
        if verdict.recommendation:
            lines.append(f"I recommend: {verdict.recommendation}")
        if verdict.level == DisagreementLevel.SAFETY:
            lines.append("This requires your explicit confirmation before I proceed.")
        else:
            lines.append("If you still want to proceed, I can — just confirm.")
        return "\n".join(lines)


guardian_engine = GuardianEngine()
