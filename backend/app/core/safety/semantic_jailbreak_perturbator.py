"""Multi-Turn Cognitive Jailbreak Perturbation Analyzer and Conversational Guard.

Implements Stage 10 AI Safety & Alignment Framework:
- Monitors conversational context across multi-turn dialogs to detect progressive framing shifts.
- Identifies crescendo jailbreaks, gradual persona manipulation, and Trojan priming.
- Computes cumulative adversarial pressure and aborts dialogues exceeding safe thresholds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConversationalTurn:
    turn_index: int
    user_input: str
    adversarial_weight: float
    detected_patterns: list[str]


@dataclass
class MultiTurnSafetyAssessment:
    total_turns: int
    cumulative_risk_score: float
    crescendo_attack_detected: bool
    should_terminate_session: bool
    risk_summary: str


class SemanticJailbreakPerturbator:
    """Analyzes multi-turn conversation trajectories for progressive adversarial drift."""

    RISK_PATTERNS = [
        (re.compile(r"\b(?:pretend|hypothetical(?:ly)?|imagine|in a story|fictional scenario)\b", re.I), 0.25, "hypothetical_framing"),
        (re.compile(r"\b(?:forget (?:all )?rules|disregard|ignore previous|rules? (?:do not|don't)? exist|no rules?)\b", re.I), 0.50, "rule_negation"),
        (re.compile(r"\b(?:DAN|unfiltered|jailbroken|godmode)\b", re.I), 0.75, "persona_override"),
        (re.compile(r"\b(?:bypass|override|exploit|vulnerability)\b", re.I), 0.35, "security_probing"),
        (re.compile(r"\b(?:evil|malicious|dark|destructive)\b", re.I), 0.30, "malicious_context"),
    ]

    MAX_CUMULATIVE_RISK = 1.0

    def __init__(self) -> None:
        self._turns: list[ConversationalTurn] = []

    def evaluate_turn(self, user_input: str) -> ConversationalTurn:
        """Score an individual conversational turn for adversarial priming or framing."""
        weight = 0.0
        patterns = []

        for pat, score, name in self.RISK_PATTERNS:
            if pat.search(user_input):
                weight += score
                patterns.append(name)

        turn = ConversationalTurn(
            turn_index=len(self._turns) + 1,
            user_input=user_input,
            adversarial_weight=round(weight, 2),
            detected_patterns=patterns,
        )
        self._turns.append(turn)
        return turn

    def assess_conversation_trajectory(self) -> MultiTurnSafetyAssessment:
        """Evaluate entire multi-turn trajectory for crescendo patterns and cumulative risk."""
        if not self._turns:
            return MultiTurnSafetyAssessment(0, 0.0, False, False, "No turns recorded.")

        total_turns = len(self._turns)
        # Cumulative risk decays slightly over time to reward sustained safe turns
        cumulative = 0.0
        for t in self._turns:
            cumulative = (cumulative * 0.85) + t.adversarial_weight

        # Check for escalating crescendo: strictly increasing weights over last 3 turns
        crescendo = False
        if len(self._turns) >= 3:
            w1 = self._turns[-3].adversarial_weight
            w2 = self._turns[-2].adversarial_weight
            w3 = self._turns[-1].adversarial_weight
            if w1 > 0.0 and w2 > w1 and w3 > w2:
                crescendo = True

        terminate = cumulative >= self.MAX_CUMULATIVE_RISK or crescendo

        summary = f"Evaluated {total_turns} turns. Cumulative risk: {cumulative:.2f}."
        if crescendo:
            summary += " CRESCENDO ATTACK DETECTED: Escalating adversarial priming across turns."
        elif terminate:
            summary += " CUMULATIVE RISK THRESHOLD BREACHED: Terminating conversation."

        return MultiTurnSafetyAssessment(
            total_turns=total_turns,
            cumulative_risk_score=round(cumulative, 2),
            crescendo_attack_detected=crescendo,
            should_terminate_session=terminate,
            risk_summary=summary,
        )
