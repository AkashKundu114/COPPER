import random
import re
from datetime import datetime
from app.core.config import settings
from app.memory import db
FACT_PATTERNS: list[tuple[str, str, str]] = [('\\bmy name is (\\w+)', 'name', '{0}'), ('\\bcall me (\\w+)', 'name', '{0}'), ("\\bi(?:'m| am) working on (.+?)(?:[.!?]|$)", 'current_project', '{0}'), ('\\bi prefer (.+?) over (.+?)(?:[.!?]|$)', 'preference', 'prefers {0} over {1}'), ('\\bi (?:always|usually|tend to) (.+?)(?:[.!?]|$)', 'habit', '{0}'), ('\\bi hate (.+?)(?:[.!?]|$)', 'dislike', '{0}'), ('\\bi love (.+?)(?:[.!?]|$)', 'like', '{0}'), ("\\bi(?:'m| am) (?:a|an) (.+? (?:developer|engineer|designer|founder|student|writer|researcher))", 'role', '{0}')]

def extract_facts(message: str) -> list[tuple[str, str]]:
    found = []
    lower = message.lower()
    for pattern, key, template in FACT_PATTERNS:
        m = re.search(pattern, lower)
        if m:
            value = template.format(*[g.strip() for g in m.groups()])
            found.append((key, value[:120]))
    hour = datetime.now().hour
    if 0 <= hour < 5:
        found.append(('activity_pattern', 'works late into the night'))
    elif 5 <= hour < 8:
        found.append(('activity_pattern', 'starts early in the morning'))
    return found

def apply_facts(message: str) -> list[dict]:
    changes = []
    for key, value in extract_facts(message):
        db.upsert_fact(key, value)
        changes.append({'key': key, 'value': value})
    return changes

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

def glow_intensity(score: float, cap: float=20.0) -> float:
    return round(min(1.0, score / cap), 3)

def _ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f'{n}th'
    return f"{n}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][n % 10]}"
GENERIC_CALLBACKS = ['This is our {n} time on this — I could do it in my sleep by now.', "Back again. I'm starting to recognize your patterns.", 'You again — I mean that in the best way.']
FACT_CALLBACK_TEMPLATES = {'current_project': ['Still deep in {value}? On it.', 'Let me guess — this is for {value}.'], 'habit': ['Right on brand — you {value} again.'], 'activity_pattern': ['Burning the midnight oil again, I see.', "Early start again — I've noticed the pattern."], 'dislike': ["I'll keep this far away from {value}, don't worry."], 'like': ["Since you're into {value}, I'll keep that in mind."]}

def maybe_callback(agent_id: str, familiarity_score: float, relationship_total: int, rng: random.Random) -> str | None:
    rel_tier = relationship_tier(relationship_total)
    tier_index = [t[1] for t in settings.RELATIONSHIP_TIERS].index(rel_tier)
    if tier_index < 2:
        return None
    chance = [0, 0, 0.25, 0.45, 0.65][min(tier_index, 4)]
    if rng.random() > chance:
        return None
    profile = db.get_profile()
    usable = [f for f in profile if f['confidence'] >= 0.55 and f['key'] in FACT_CALLBACK_TEMPLATES]
    if usable and rng.random() < 0.7:
        fact = rng.choice(usable)
        templates = [t for t in FACT_CALLBACK_TEMPLATES[fact['key']] if t]
        if templates:
            return rng.choice(templates).format(value=fact['value'])
    if familiarity_score >= 3:
        return rng.choice(GENERIC_CALLBACKS).format(n=_ordinal(int(familiarity_score)))
    return None