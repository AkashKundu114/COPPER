"""
learner.py
===========
The "the more we work together, the more it knows me" engine. Two jobs:

1. extract_facts(message) — cheap regex/heuristic extraction of durable
   facts from what the user says ("I'm working on X", "I prefer X over Y",
   late-night activity patterns, etc). Each fact is upserted into
   user_profile with a confidence score that grows on repetition.

2. familiarity tier + callback line generation — every agent invocation
   bumps that agent's familiarity_score. Past certain thresholds, replies
   start referencing stored facts or the agent's own invocation count —
   the "inside joke" behavior from the brief. Probability and specificity
   of callbacks scale with the relationship tier, so it starts subtle and
   gets more personal over time rather than being random from turn one.

This is intentionally simple and transparent (no LLM call) — swapping in
real NLU/LLM-based extraction is a drop-in replacement for extract_facts().
"""

import random
import re
from datetime import datetime

from app.core.config import settings
from app.memory import db

# ── Fact extraction patterns ─────────────────────────────────────────────────
# (regex, key, value_template) — {0}, {1}... map to regex groups
FACT_PATTERNS: list[tuple[str, str, str]] = [
    (r"\bmy name is (\w+)", "name", "{0}"),
    (r"\bcall me (\w+)", "name", "{0}"),
    (r"\bi(?:'m| am) working on (.+?)(?:[.!?]|$)", "current_project", "{0}"),
    (r"\bi prefer (.+?) over (.+?)(?:[.!?]|$)", "preference", "prefers {0} over {1}"),
    (r"\bi (?:always|usually|tend to) (.+?)(?:[.!?]|$)", "habit", "{0}"),
    (r"\bi hate (.+?)(?:[.!?]|$)", "dislike", "{0}"),
    (r"\bi love (.+?)(?:[.!?]|$)", "like", "{0}"),
    (r"\bi(?:'m| am) (?:a|an) (.+? (?:developer|engineer|designer|founder|student|writer|researcher))", "role", "{0}"),
]


def extract_facts(message: str) -> list[tuple[str, str]]:
    """Returns [(key, value), ...] found in this message."""
    found = []
    lower = message.lower()
    for pattern, key, template in FACT_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            value = template.format(*[g.strip() for g in m.groups()])
            found.append((key, value[:120]))

    # Time-of-day pattern (derived, not regex-based)
    hour = datetime.now().hour
    if 0 <= hour < 5:
        found.append(("activity_pattern", "works late into the night"))
    elif 5 <= hour < 8:
        found.append(("activity_pattern", "starts early in the morning"))

    return found


def apply_facts(message: str) -> list[dict]:
    """Extracts facts from a message, persists them, returns what changed."""
    changes = []
    for key, value in extract_facts(message):
        db.upsert_fact(key, value)
        changes.append({"key": key, "value": value})
    return changes


# ── Familiarity tiers ─────────────────────────────────────────────────────────
def agent_tier(score: float) -> str:
    label = settings.AGENT_TIERS[0][1]
    for threshold, name in settings.AGENT_TIERS:
        if score >= threshold:
            label = name
    return label


def relationship_tier(total: int) -> str:
    label = settings.RELATIONSHIP_TIERS[0][1]
    for threshold, name in settings.RELATIONSHIP_TIERS:
        if total >= threshold:
            label = name
    return label


def glow_intensity(score: float, cap: float = 20.0) -> float:
    """0..1 node glow strength for the brain visualization."""
    return round(min(1.0, score / cap), 3)


# ── Callback / inside-joke generation ────────────────────────────────────────
def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd','th','th','th','th','th','th'][n % 10]}"


GENERIC_CALLBACKS = [
    "This is our {n} time on this — I could do it in my sleep by now.",
    "Back again. I'm starting to recognize your patterns.",
    "You again — I mean that in the best way.",
]

FACT_CALLBACK_TEMPLATES = {
    "current_project": [
        "Still deep in {value}? On it.",
        "Let me guess — this is for {value}.",
    ],
    "habit": [
        "Right on brand — you {value} again.",
    ],
    "activity_pattern": [
        "Burning the midnight oil again, I see.",
        "Early start again — I've noticed the pattern.",
    ],
    "dislike": [
        "I'll keep this far away from {value}, don't worry.",
    ],
    "like": [
        "Since you're into {value}, I'll keep that in mind.",
    ],
}


def maybe_callback(agent_id: str, familiarity_score: float, relationship_total: int, rng: random.Random) -> str | None:
    """
    Decide whether this response should include a memory callback, and
    build it. Probability and personalization depth scale with how well
    COPPER knows the user overall (relationship tier), not just this one
    agent, so the whole system feels like it's learning, not just one node.
    """
    rel_tier = relationship_tier(relationship_total)
    tier_index = [t[1] for t in settings.RELATIONSHIP_TIERS].index(rel_tier)

    # Stranger / Getting Acquainted: no callbacks yet — hasn't earned it
    if tier_index < 2:
        return None

    # Probability grows with relationship depth
    chance = [0, 0, 0.25, 0.45, 0.65][min(tier_index, 4)]
    if rng.random() > chance:
        return None

    profile = db.get_profile()
    usable = [f for f in profile if f["confidence"] >= 0.55 and f["key"] in FACT_CALLBACK_TEMPLATES]

    if usable and rng.random() < 0.7:
        fact = rng.choice(usable)
        templates = [t for t in FACT_CALLBACK_TEMPLATES[fact["key"]] if t]
        if templates:
            return rng.choice(templates).format(value=fact["value"])

    if familiarity_score >= 3:
        return rng.choice(GENERIC_CALLBACKS).format(n=_ordinal(int(familiarity_score)))

    return None
