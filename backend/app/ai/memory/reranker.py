import asyncio
import json
import re
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger

RE_RANKER_SYSTEM_PROMPT = """You are a relevance judge for a retrieval system.
Evaluate how relevant the retrieved passage is to answering the user query.
Score strictly between 0.0 (irrelevant) and 1.0 (directly answers the query with high factual accuracy).
Respond ONLY with a valid JSON object:
{"relevance": 0.85, "reasoning": "brief explanation"}"""


class LocalReRanker:
    """
    Local Cross-Encoder Re-Ranker using a micro-model (e.g. Qwen2.5-0.5B / mini-model).
    Takes top-K (default K=10) candidates from hybrid retrieval, evaluates (query, passage)
    relevance on a 0.0–1.0 scale, and returns top-N (default N=5) re-ranked candidates.
    """

    def __init__(self, model_tag: str | None = None):
        self._custom_model_tag = model_tag
        self.fallback_model = "qwen2.5:0.5b"

    def get_model(self) -> str:
        if self._custom_model_tag:
            return self._custom_model_tag
        try:
            return model_manager.get_mini_model(prefer_tag=True)
        except Exception:
            return self.fallback_model

    async def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_n: int = 5,
        max_concurrency: int = 4,
    ) -> list[dict[str, Any]]:
        """
        Re-ranks top-K candidate passages against the query.
        Returns top-N sorted descending by relevance score (0.0 to 1.0).
        """
        if not candidates:
            return []

        # If candidates are already fewer than or equal to 1, assign baseline relevance
        if len(candidates) == 1:
            c = dict(candidates[0])
            c["relevance_score"] = c.get("relevance_score", 0.90)
            return [c]

        # Check if Ollama is available for LLM cross-encoder scoring
        ollama_active = False
        try:
            ollama_active = await ollama_client.is_available()
        except Exception:
            ollama_active = False

        semaphore = asyncio.Semaphore(max_concurrency)

        async def _score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
            passage = candidate.get("content", "")
            item = dict(candidate)

            if ollama_active and len(passage.strip()) > 10:
                async with semaphore:
                    try:
                        score, reason = await self._score_with_llm(query, passage)
                        item["relevance_score"] = round(score, 3)
                        item["rerank_reasoning"] = reason
                        return item
                    except Exception as err:
                        logger.debug(f"LLM rerank scoring failed for candidate, using heuristic: {err}")

            # Fallback heuristic scoring
            score, reason = self._score_heuristic(query, passage, candidate)
            item["relevance_score"] = round(score, 3)
            item["rerank_reasoning"] = reason
            return item

        # Evaluate candidate passages
        tasks = [_score_candidate(c) for c in candidates]
        scored_results = await asyncio.gather(*tasks)

        # Sort by relevance_score descending
        scored_results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        return scored_results[:top_n]

    async def _score_with_llm(self, query: str, passage: str) -> tuple[float, str]:
        """Queries the micro-model to score relevance on 0.0–1.0 scale."""
        model_name = self.get_model()
        snippet = passage[:600].strip()

        messages = [
            {"role": "system", "content": RE_RANKER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Query: {query}\n\nPassage:\n{snippet}\n\nRate relevance from 0.0 to 1.0 in JSON.",
            },
        ]

        raw = await ollama_client.chat(messages, model=model_name)

        # Extract and parse JSON
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
        if "{" in clean and "}" in clean:
            s_idx = clean.index("{")
            e_idx = clean.rindex("}") + 1
            data = json.loads(clean[s_idx:e_idx])
            relevance = float(data.get("relevance", 0.5))
            reasoning = str(data.get("reasoning", "Cross-encoder micro-model evaluation."))
            return max(0.0, min(1.0, relevance)), reasoning

        raise ValueError("Could not parse JSON from micro-model response")

    def _score_heuristic(
        self, query: str, passage: str, candidate: dict[str, Any]
    ) -> tuple[float, str]:
        """
        Calibrated lexical & rank prior heuristic fallback:
        Combines token coverage, term density, vector similarity, and RRF rank prior.
        """
        q_tokens = re.findall(r"\w+", query.lower())
        p_tokens = re.findall(r"\w+", passage.lower())

        if not q_tokens or not p_tokens:
            return 0.50, "Neutral fallback prior."

        q_set = set(q_tokens)
        p_set = set(p_tokens)

        # 1. Query term overlap ratio (what % of query words appear in passage)
        overlap = len(q_set & p_set)
        coverage = overlap / max(1, len(q_set))

        # 2. Exact phrase boost
        exact_boost = 0.20 if query.lower().strip() in passage.lower() else 0.0

        # 3. Prior signals from hybrid retrieval
        vec_sim = float(candidate.get("vector_similarity") or 0.50)
        rrf_prior = min(0.30, float(candidate.get("rrf_score") or 0.0) * 8.0)

        # Weighted composite score
        score = (0.45 * coverage) + (0.25 * vec_sim) + (0.20 * rrf_prior) + exact_boost
        clamped = max(0.10, min(0.98, score))
        return clamped, "Calibrated hybrid cross-feature heuristic."


reranker = LocalReRanker()
