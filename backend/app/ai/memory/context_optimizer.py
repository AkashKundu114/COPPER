"""Context Optimization & Token Budget Allocation Engine for C.O.P.P.E.R.

Eliminates duplicate facts across Profile, GraphRAG, and Vector stores,
and applies token-budget enforcement and relevance pruning to protect LLM context windows.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from app.core.logger import logger


@dataclass(frozen=True)
class OptimizedContextResult:
    optimized_text: str
    original_estimated_tokens: int
    optimized_estimated_tokens: int
    tokens_saved: int
    duplicates_removed: int
    pruned_entries: int


class ContextOptimizer:
    """Optimizes context snippets before feeding into model prompt templates."""

    def __init__(self, default_token_budget: int = 3072):
        self.default_token_budget = default_token_budget

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic estimation of tokens (~4 characters per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def _normalize_fact(fact_text: str) -> str:
        """Normalizes fact text for fuzzy deduplication."""
        cleaned = re.sub(r"\[MEMORY\b[^\]]*?\]:?", "", fact_text)
        cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned.strip())
        return " ".join(cleaned.lower().split())

    def deduplicate_facts(self, facts: list[str]) -> tuple[list[str], int]:
        """Removes exact and semantic near-duplicate facts."""
        seen_hashes: set[str] = set()
        unique_facts: list[str] = []
        dupes_removed = 0

        for f in facts:
            norm = self._normalize_fact(f)
            if not norm or len(norm) < 5:
                continue
            h = hashlib.sha256(norm.encode("utf-8")).hexdigest()
            if h in seen_hashes:
                dupes_removed += 1
                continue
            seen_hashes.add(h)
            unique_facts.append(f)

        return unique_facts, dupes_removed

    def optimize_context(
        self,
        context_parts: list[str],
        token_budget: int | None = None,
    ) -> OptimizedContextResult:
        """Deduplicates facts and enforces strict token budget constraints."""
        budget = token_budget or self.default_token_budget
        raw_full_text = "\n\n".join(p for p in context_parts if p.strip())
        orig_tokens = self.estimate_tokens(raw_full_text)

        # 1. Split lines into atomic units
        raw_lines = [line.strip() for line in raw_full_text.splitlines() if line.strip()]
        unique_lines, dupes_count = self.deduplicate_facts(raw_lines)

        # 2. Budget enforcement (relevance preservation from top to bottom)
        allocated_lines: list[str] = []
        pruned_count = 0

        for line in unique_lines:
            candidate_text = "\n".join(allocated_lines + [line])
            if self.estimate_tokens(candidate_text) <= budget:
                allocated_lines.append(line)
            else:
                pruned_count += 1

        optimized_text = "\n".join(allocated_lines)
        opt_tokens = self.estimate_tokens(optimized_text)
        saved = max(0, orig_tokens - opt_tokens)

        logger.debug(
            f"[ContextOptimizer] Optimized prompt context: {orig_tokens} -> {opt_tokens} tokens "
            f"(Saved {saved} tokens, removed {dupes_count} dupes, pruned {pruned_count} items)"
        )

        return OptimizedContextResult(
            optimized_text=optimized_text,
            original_estimated_tokens=orig_tokens,
            optimized_estimated_tokens=opt_tokens,
            tokens_saved=saved,
            duplicates_removed=dupes_count,
            pruned_entries=pruned_count,
        )


context_optimizer = ContextOptimizer()
