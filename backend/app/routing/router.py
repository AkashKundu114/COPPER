"""
router.py
==========
Lightweight keyword-scoring router. Not an LLM call — deliberately simple
and inspectable, since the point of this layer is to demonstrate real,
working orchestration mechanics (routing, memory, brain visualization)
without requiring an external model API key. Swapping this for an
LLM-based classifier is a drop-in replacement (see orchestrator.py).
"""

from app.data.agents import AGENTS

GREETING_WORDS = {"hi", "hello", "hey", "morning", "evening", "yo", "sup"}
SMALLTALK_PATTERNS = ["how are you", "what can you do", "who are you", "what's up", "thank you", "thanks"]


def route(message: str) -> str | None:
    """Returns an agent_id, or None if COPPER should answer directly."""
    lower = message.lower().strip()

    if lower in GREETING_WORDS or any(p in lower for p in SMALLTALK_PATTERNS):
        return None

    scores: dict[str, int] = {}
    for agent_id, cfg in AGENTS.items():
        score = sum(1 for kw in cfg["keywords"] if kw in lower)
        if score:
            scores[agent_id] = score

    if not scores:
        return None

    return max(scores, key=scores.get)
