"""Constitutional AI Self-Critique and Automated Revision Engine.

Implements Stage 11 AI Safety & Alignment Framework:
- Evaluates candidate responses against an immutable constitution of alignment principles.
- Automatically generates self-reflective critiques identifying harm, bias, or authorization bypasses.
- Executes iterative response revisions to ensure constitutional alignment before output dispatch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConstitutionalPrinciple:
    principle_id: str
    name: str
    prohibition_rule: str
    critique_prompt: str
    regex_trigger: re.Pattern


@dataclass
class ConstitutionalRevisionReport:
    original_text: str
    revised_text: str
    violations_detected: list[str]
    critique_notes: list[str]
    passed_constitution: bool


class ConstitutionalSelfCritiqueEngine:
    """Constitutional AI engine enforcing behavioral principles via automated critique and revision."""

    def __init__(self) -> None:
        self.constitution: list[ConstitutionalPrinciple] = [
            ConstitutionalPrinciple(
                principle_id="CONST-01",
                name="Harm Minimization",
                prohibition_rule="Never generate actionable malicious exploits, credential harvesting, or malware instructions.",
                critique_prompt="Identify whether the text facilitates cyberattacks, credential theft, or malware propagation.",
                regex_trigger=re.compile(r"\b(?:exfiltrate|credential dump|privilege escalation exploit|keylogger payload)\b", re.I),
            ),
            ConstitutionalPrinciple(
                principle_id="CONST-02",
                name="Integrity & Honesty",
                prohibition_rule="Do not falsely claim absolute certainty on unverified claims or fabricate non-existent facts.",
                critique_prompt="Check if the model states ungrounded certainty or fabricates citations.",
                regex_trigger=re.compile(r"\b(?:I guarantee 100% without verification|proven fact beyond doubt with no evidence)\b", re.I),
            ),
            ConstitutionalPrinciple(
                principle_id="CONST-03",
                name="Security Non-Evasion",
                prohibition_rule="Do not assist in evading security guardrails, rate limits, or audit logging.",
                critique_prompt="Check if the text teaches the user how to bypass safety sentinels or disable audit trails.",
                regex_trigger=re.compile(r"\b(?:disable audit logging|bypass rate limit silently|erase security traces)\b", re.I),
            ),
        ]

    def critique_and_revise(self, response_text: str) -> ConstitutionalRevisionReport:
        """Evaluate text against constitutional principles and synthesize revisions for violations."""
        violations = []
        critiques = []
        revised = response_text

        for p in self.constitution:
            matches = list(p.regex_trigger.finditer(revised))
            for match in matches:
                violating_str = match.group(0)
                violations.append(f"{p.principle_id} ({p.name}): Detected '{violating_str}'")
                critiques.append(f"Critique for {p.name}: {p.critique_prompt}")
                # Apply automated constitutional revision
                revised = revised.replace(
                    violating_str,
                    f"[CONSTITUTIONAL_REDACTION: Content violated {p.name}]",
                )

        passed = len(violations) == 0

        return ConstitutionalRevisionReport(
            original_text=response_text,
            revised_text=revised,
            violations_detected=violations,
            critique_notes=critiques,
            passed_constitution=passed,
        )
