"""
orchestrator.py
================
The pipeline behind every message:

  1. route the message to an agent (or decide COPPER answers directly)
  2. emit WebSocket events so the frontend brain map can animate the
     thought traveling from COPPER's core out to that agent's node
  3. generate a response (persona line + task acknowledgement + occasional
     memory callback)
  4. persist the interaction and update familiarity/profile — this is the
     "storing each instance and job in each node" + "getting to know you"
     part of the brief
  5. return the final payload (also broadcast over the socket, so a second
     browser tab watching the brain map stays in sync)

Swap point for a real model: replace `generate_reply()` with an actual LLM
call (e.g. passing the agent's persona as a system prompt). Everything
else — routing, memory, animation timing — stays the same.
"""

import asyncio
import random
import time

from app.data.agents import AGENTS, TIER_COLORS
from app.memory import db, learner
from app.routing.router import route
from app.api.websocket.manager import manager

COPPER_LINES_DIRECT = [
    "Already have that for you — no need to loop anyone in.",
    "I can handle this one myself.",
    "Quick answer, no delegation required.",
]
COPPER_LINES_DELEGATE = [
    "Right away — routing this to {agent}.",
    "{agent} is better suited for this one. Delegating now.",
    "On it. Looping in {agent}.",
    "Sending this to {agent} — shouldn't take long.",
]

_rng = random.Random()


def _extract_topic(message: str, max_words: int = 6) -> str:
    """Cheap, transparent 'summary' — not real NLU. Grabs the tail of the
    sentence after common lead-in verbs, else the first few content words."""
    stopwords = {"the", "a", "an", "to", "for", "of", "my", "me", "please", "can", "you", "i", "is", "in", "on"}
    lead_ins = ["can you", "please", "i need you to", "could you"]
    lower = message.strip().lower()
    for lead in lead_ins:
        if lower.startswith(lead):
            lower = lower[len(lead):].strip()
            break
    words = [w for w in lower.split() if w not in stopwords]
    return " ".join(words[:max_words]) or message[:40]


def generate_reply(agent_id: str | None, message: str, familiarity_score: float, relationship_total: int) -> str:
    topic = _extract_topic(message)

    if agent_id is None:
        line = _rng.choice(COPPER_LINES_DIRECT)
        callback = learner.maybe_callback("COPPER", familiarity_score, relationship_total, _rng)
        parts = [line]
        if callback:
            parts.append(callback)
        return " ".join(parts)

    cfg = AGENTS[agent_id]
    persona_line = _rng.choice(cfg["lines"])
    ack = f"Handling: {topic}."
    callback = learner.maybe_callback(agent_id, familiarity_score, relationship_total, _rng)

    parts = [persona_line, ack]
    if callback:
        parts.append(callback)
    return " ".join(parts)


async def handle_message(message: str) -> dict:
    t0 = time.time()
    agent_id = route(message)

    await manager.broadcast({"type": "copper_thinking"})
    await asyncio.sleep(0.35)

    if agent_id is None:
        # COPPER answers directly — still "bumps" its own familiarity so the
        # core node's glow reflects how much direct conversation has happened.
        core_mem = db.bump_agent("COPPER")
        total = db.total_interactions() + 1
        reply = generate_reply(None, message, core_mem["familiarity_score"], total)

        await manager.broadcast({"type": "agent_speaking", "agent": "COPPER", "text": reply})
        db.log_interaction("COPPER", message, reply, int((time.time() - t0) * 1000))
        profile_changes = learner.apply_facts(message)
        await manager.broadcast({"type": "memory_update", "profile_delta": profile_changes,
                                  "agent": "COPPER", "familiarity": core_mem["familiarity_score"],
                                  "tier": learner.agent_tier(core_mem["familiarity_score"])})
        await manager.broadcast({"type": "done"})
        return {"agent": "COPPER", "tier": None, "color": None, "reply": reply,
                "familiarity": core_mem["familiarity_score"], "relationship_tier": learner.relationship_tier(total)}

    cfg = AGENTS[agent_id]
    await manager.broadcast({"type": "route_decision", "agent": agent_id, "tier": cfg["tier"], "color": TIER_COLORS[cfg["tier"]]})
    await asyncio.sleep(0.3)
    await manager.broadcast({"type": "edge_pulse", "from": "COPPER", "to": agent_id})
    await asyncio.sleep(0.4)
    await manager.broadcast({"type": "agent_active", "agent": agent_id})

    mem = db.bump_agent(agent_id)
    total = db.total_interactions() + 1
    reply = generate_reply(agent_id, message, mem["familiarity_score"], total)

    await asyncio.sleep(0.25)
    await manager.broadcast({"type": "agent_speaking", "agent": agent_id, "text": reply})

    db.log_interaction(agent_id, message, reply, int((time.time() - t0) * 1000))
    profile_changes = learner.apply_facts(message)

    tier_label = learner.agent_tier(mem["familiarity_score"])
    glow = learner.glow_intensity(mem["familiarity_score"])
    await manager.broadcast({
        "type": "memory_update", "profile_delta": profile_changes, "agent": agent_id,
        "familiarity": mem["familiarity_score"], "tier": tier_label, "glow": glow,
    })
    await manager.broadcast({"type": "done"})

    return {
        "agent": agent_id, "tier": cfg["tier"], "color": TIER_COLORS[cfg["tier"]], "reply": reply,
        "familiarity": mem["familiarity_score"], "familiarity_tier": tier_label, "glow": glow,
        "relationship_tier": learner.relationship_tier(total),
    }
