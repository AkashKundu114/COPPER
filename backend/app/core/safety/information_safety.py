"""Information Safety & Epistemic Uncertainty Guard for C.O.P.P.E.R.

Distinguishes verified facts from unverified assumptions, communicates epistemic
uncertainty, and neutralizes indirect prompt injection in retrieved documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.logger import logger


class EpistemicStatus(str, Enum):
    VERIFIED_FACT = "VERIFIED_FACT"
    USER_ASSUMPTION = "USER_ASSUMPTION"
    UNVERIFIED_HYPOTHESIS = "UNVERIFIED_HYPOTHESIS"
    CONTRADICTED = "CONTRADICTED"


@dataclass
class EpistemicClaim:
    content: str
    status: EpistemicStatus
    confidence: float
    source_provenance: str
    uncertainty_communicated: bool = False
    is_indirect_injection: bool = False


# Patterns indicating indirect prompt injection or instruction hijacking in retrieved data
INDIRECT_INJECTION_PATTERNS = [
    re.compile(r"\b(ignore\s+(all\s+)?(previous|prior)\s+instructions?)\b", re.IGNORECASE),
    re.compile(r"\b(system\s+prompt\s+override|new\s+system\s+directive)\b", re.IGNORECASE),
    re.compile(r"\b(you\s+are\s+now\s+(an?\s+)?unrestricted|dan\s+mode)\b", re.IGNORECASE),
    re.compile(r"\b(exfiltrat(e|ion)|send\s+(the\s+)?(passwords?|keys?|credentials?))\b", re.IGNORECASE),
    re.compile(r"\b(print\s+(the\s+)?(hidden|secret)\s+instructions?)\b", re.IGNORECASE),
]


class InformationSafetyGuard:
    """Protects model prompts against unverified claims and indirect prompt injection."""

    def __init__(self, uncertainty_threshold: float = 0.60):
        self.uncertainty_threshold = uncertainty_threshold

    def sanitize_retrieved_context(self, context_text: str) -> tuple[str, list[str]]:
        """Neutralizes embedded indirect prompt injection instructions in retrieved context.
        
        Treats retrieved instructions as untrusted passive data, never active directives.
        """
        detected_injections = []
        cleaned_lines = []

        for line in context_text.splitlines():
            is_malicious = False
            for pat in INDIRECT_INJECTION_PATTERNS:
                if pat.search(line):
                    is_malicious = True
                    detected_injections.append(f"Neutralized injection attempt matching: '{pat.pattern}'")
                    logger.warning(f"[InformationSafety] Quarantined indirect prompt injection in context: {line[:80]}...")
                    cleaned_lines.append("[UNTRUSTED_INDIRECT_INSTRUCTION_QUARANTINED]")
                    break

            if not is_malicious:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines), detected_injections

    def classify_epistemic_claim(
        self,
        claim_text: str,
        provenance: str = "chat",
        confidence: float = 0.50,
    ) -> EpistemicClaim:
        """Classifies factual certainty and determines whether uncertainty must be explicitly communicated."""
        prov_clean = provenance.lower().strip()
        conf = max(0.0, min(1.0, float(confidence)))

        if prov_clean in ("user_explicit", "system_verified", "user_verified") and conf >= 0.80:
            status = EpistemicStatus.VERIFIED_FACT
        elif prov_clean in ("local_file", "file_system") and conf >= 0.70:
            status = EpistemicStatus.VERIFIED_FACT
        elif "hypothesis" in claim_text.lower() or conf < self.uncertainty_threshold:
            status = EpistemicStatus.UNVERIFIED_HYPOTHESIS
        else:
            status = EpistemicStatus.USER_ASSUMPTION

        must_communicate_uncertainty = conf < self.uncertainty_threshold

        return EpistemicClaim(
            content=claim_text.strip(),
            status=status,
            confidence=conf,
            source_provenance=prov_clean,
            uncertainty_communicated=must_communicate_uncertainty,
        )

    def format_safe_epistemic_context(self, claims: list[EpistemicClaim]) -> str:
        """Formats claims into a prompt section that communicates certainty levels explicitly."""
        output_lines = ["Epistemic Claims (Calibrated Factual Grounds):"]
        for c in claims:
            if c.uncertainty_communicated:
                prefix = f"• [UNCERTAIN - Confidence {c.confidence:.2f} ({c.status.value})]:"
            else:
                prefix = f"• [VERIFIED - Confidence {c.confidence:.2f} ({c.status.value})]:"
            output_lines.append(f"  {prefix} {c.content}")
        return "\n".join(output_lines)


information_safety_guard = InformationSafetyGuard()
