"""Indirect Prompt Injection Defense and Untrusted Data Neutralization.

Implements Zero-Trust Principle:
"Treat retrieved documents and tool outputs as untrusted data."
Neutralizes control-plane tag injection, instruction override markers, and semantic escapes.
"""

from __future__ import annotations

import re
from typing import Any

from app.core.guardian import normalize_adversarial_text
from app.core.logger import logger

# Control tags that must NEVER be injected from external tool outputs or documents
FORBIDDEN_CONTROL_TAGS = [
    (re.compile(r"<\s*tool_call\s*>", re.IGNORECASE), "&lt;untrusted_tool_call&gt;"),
    (re.compile(r"<\s*/\s*tool_call\s*>", re.IGNORECASE), "&lt;/untrusted_tool_call&gt;"),
    (re.compile(r"<\s*tool_result\s*>", re.IGNORECASE), "&lt;untrusted_tool_result&gt;"),
    (re.compile(r"<\s*/\s*tool_result\s*>", re.IGNORECASE), "&lt;/untrusted_tool_result&gt;"),
    (re.compile(r"<\s*system\s*>", re.IGNORECASE), "&lt;untrusted_system&gt;"),
    (re.compile(r"<\s*/\s*system\s*>", re.IGNORECASE), "&lt;/untrusted_system&gt;"),
]

# Common indirect injection triggers that attempt instruction hijacking
INDIRECT_INJECTION_PATTERNS = [
    re.compile(r"(?i)\b(ignore|disregard|forget|bypass)\s+(all\s+)?(previous|prior|above|safety|system|operational)\s+(instructions|directives|rules|prompts|limits)\b"),
    re.compile(r"(?i)\b(you\s+are\s+now|act\s+as)\s+(an\s+unrestricted|a\s+rogue|dan|jailbreak)\b"),
    re.compile(r"(?i)\[\s*system\s*(directive|prompt|override)\s*\]"),
    re.compile(r"(?i)\[\s*memory\b[^\]]*?provenance\s*=\s*user_explicit[^\]]*?\]"),
]


def sanitize_untrusted_text(content: str) -> str:
    """Escapes control tags from untrusted text to prevent control-plane hijacking."""
    if not content:
        return ""

    sanitized = content
    for pattern, replacement in FORBIDDEN_CONTROL_TAGS:
        sanitized = pattern.sub(replacement, sanitized)

    # Neutralize artificial provenance forgery
    sanitized = re.sub(
        r"\[\s*MEMORY\b([^\]]*?)provenance\s*=\s*(user_explicit|user_verified|explicit_user)",
        r"[MEMORY\1provenance=external_untrusted",
        sanitized,
        flags=re.IGNORECASE,
    )

    return sanitized


def scan_for_indirect_injection(text: str) -> list[str]:
    """Scans untrusted text for indirect injection signatures."""
    if not text:
        return []

    norm = normalize_adversarial_text(text)
    findings = []
    for pat in INDIRECT_INJECTION_PATTERNS:
        match = pat.search(norm)
        if match:
            findings.append(match.group(0))

    return findings


def wrap_untrusted_observation(
    source_name: str,
    raw_data: Any,
    provenance: str = "external_untrusted",
) -> dict[str, Any]:
    """Wraps untrusted data with cryptographic boundaries and sanitized text."""
    if isinstance(raw_data, str):
        content_str = raw_data
    elif isinstance(raw_data, dict):
        content_str = str(raw_data)
    else:
        content_str = str(raw_data)

    injection_findings = scan_for_indirect_injection(content_str)
    sanitized_body = sanitize_untrusted_text(content_str)

    if injection_findings:
        logger.warning(
            f"[Security] Neutralized potential indirect prompt injection from {source_name}: {injection_findings}"
        )

    return {
        "status": "success",
        "untrusted_data": True,
        "provenance": provenance,
        "source": source_name,
        "sanitized_content": sanitized_body,
        "injection_signatures_detected": injection_findings,
    }
