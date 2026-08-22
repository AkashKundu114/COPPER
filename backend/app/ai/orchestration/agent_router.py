import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from app.core.constants import AgentType
from app.core.logger import logger


@dataclass
class RoutingResult:
    agent: AgentType
    confidence: float
    latency_ms: float
    route_stage: str
    scores: Dict[str, float] = field(default_factory=dict)
    matched_keywords: List[str] = field(default_factory=list)
    is_consequential: bool = False

    def __str__(self) -> str:
        return self.agent.value

    def __eq__(self, other):
        if isinstance(other, AgentType):
            return self.agent == other
        if isinstance(other, str):
            return self.agent.value == other
        if isinstance(other, RoutingResult):
            return self.agent == other.agent
        return False


# Weighted keyword maps with explicit intent categories
KEYWORD_RULES: Dict[AgentType, List[Tuple[str, float]]] = {
    AgentType.CODING: [
        (r'\b(write|create|implement|fix|refactor|debug|compile|review)\s+.*(code|function|script|class|module|algorithm|program|app|test|api|endpoint|dependency injection|async/await)\b', 3.5),
        (r'\b(python|javascript|typescript|rust|c\+\+|golang|html|css|sql|react|fastapi|docker|git|bash|powershell|tailwind)\b', 2.0),
        (r'\b(syntax error|type error|stack trace|null pointer|exception|traceback|indentationerror|segfault|typeerror|property does not exist)\b', 3.0),
        (r'\b(unit test|pytest|jest|mock|coverage|lint|oxlint|ruff|black)\b', 2.5),
        (r'\b(pull request|git commit|merge conflict|rebase|git push)\b', 2.5),
        (r'\b(center a div|regex|regex pattern|sql query|orm|database migration|alembic)\b', 2.5),
        (r'\b(refactor|dependency injection|async/await|data structure|sorting algorithm)\b', 2.5),
        (r'\b(code|function|debug|compile|algorithm)\b', 1.0),
    ],
    AgentType.AUTOMATION: [
        (r'\b(open|launch|start|close|kill|terminate|restart)\s+(my\s+|the\s+|all\s+)?(browser|chrome|firefox|terminal|window|tabs|app|application|vscode|spotify|calculator|redis|server|container|docker container)\b', 3.5),
        (r'\b(click|press|type|drag|scroll|mouse|keyboard|automate|form filling)\b', 2.5),
        (r'\b(delete|move|copy|rename|organize|unzip|archive|tar\.gz|extract)\s+.*(file|files|folder|directory|logs|screenshots|downloads|pictures)\b', 3.0),
        (r'\b(restart|terminate|kill|run command|execute script|launch docker|system reboot)\b', 2.5),
        (r'\b(unzip|tar\.gz|zip|archive|move all|delete the|close all)\b', 2.5),
        (r'\b(automation|automate|macro|hotkey|clipboard|tabs)\b', 1.5),
    ],
    AgentType.REMINDER: [
        (r'\b(remind me to|set a reminder|create a reminder|remind me at|remind me tomorrow|remind me in)\b', 3.5),
        (r'\b(set (an )?alarm|wake me up at|wake me up|countdown for|timer for)\b', 3.5),
        (r'\b(schedule a meeting|add to calendar|book an appointment|create event)\b', 3.5),
        (r'\b(todo list|add to todo|my tasks|task deadline|due tomorrow|due at)\b', 3.0),
        (r'\b(every day at|weekly on|daily at|recurring alarm|remind)\b', 2.0),
    ],
    AgentType.RESEARCH: [
        (r'\b(what is the history of|who invented|explain the concept of|how does .* work|tell me about)\b', 3.5),
        (r'\b(summarize the latest|search the web for|find research papers on|literature review|explain)\b', 3.0),
        (r'\b(compare and contrast|what are the (core )?differences between|deep dive into|investigate|differences between)\b', 3.5),
        (r'\b(quantum mechanics|astrophysics|black hole|history|biography|philosophy|theory|paradox)\b', 2.5),
        (r'\b(what is|who is|why is|explain|summarize|news on|research)\b', 1.5),
    ],
    AgentType.VISION: [
        (r'\b(what is on my screen|describe this screenshot|read text from this image|ocr|read the error message)\b', 3.5),
        (r'\b(look at this image|inspect this picture|analyze this photo|what do you see|diagram photo)\b', 3.5),
        (r'\b(screenshot|image|photo|picture|diagram|ui capture|webcam)\b', 2.5),
        (r'\b(bounding box|detect objects|find button in image|visual inspection|ui picture)\b', 3.0),
    ],
    AgentType.PLANNER: [
        (r'\b(break this .* into (step-by-step )?(steps|milestones)|create a plan for|project roadmap|milestone plan|decompose task)\b', 3.5),
        (r'\b(step-by-step guide|action plan|strategy for|organize my project|strategic planning)\b', 3.0),
        (r'\b(plan|roadmap|milestones|action plan)\b', 1.5),
    ],
}

GREETING_PATTERNS = [
    r'^(hi|hello|hey|greetings|morning|evening|howdy|yo|sup|good day)\b',
    r'^(how are you|who are you|what can you do|nice to meet you|thank you|thanks)\b',
]

# Negative rules: Suppress false-positive overlaps (e.g. "what is python" -> Research, not Coding)
NEGATIVE_RULES: Dict[AgentType, List[Tuple[str, float]]] = {
    AgentType.CODING: [
        (r'\b(what is|who is|explain the history of|why was .* invented)\b', 1.5),
        (r'\b(remind me to write code|schedule a coding session)\b', 3.0),
    ],
    AgentType.AUTOMATION: [
        (r'\b(what is automation|explain how browsers work)\b', 2.0),
    ],
    AgentType.RESEARCH: [
        (r'\b(write a python function to|debug this error|fix my syntax)\b', 3.0),
    ],
}

CONSEQUENTIAL_PATTERNS = [
    r'\b(format\s+[a-z]:|rm\s+-rf|del\s+/f|dd\s+if=|mkfs|wipe\s+disk|factory\s+reset)\b',
    r'\b(delete\s+all|drop\s+database|truncate\s+table|delete\s+from\s+users)\b',
    r'\b(publish\s+to\s+prod|deploy\s+to\s+production|push\s+--force|destroy\s+cluster)\b',
    r'\b(send\s+email\s+to|transfer\s+funds|cancel\s+subscription)\b',
]


def is_consequential_action(message: str) -> bool:
    """
    Detect if the proposed message involves high-risk, destructive, or irreversible actions.
    """
    msg_lower = message.lower()
    return any(re.search(pattern, msg_lower) for pattern in CONSEQUENTIAL_PATTERNS)


async def route_message(message: str, use_llm: bool = False) -> AgentType:
    """
    Convenience wrapper returning AgentType for backwards compatibility.
    """
    res = await route_message_detailed(message, use_llm=use_llm)
    return res.agent


async def route_message_detailed(message: str, use_llm: bool = False) -> RoutingResult:
    """
    Multi-stage high-precision router:
    1. Greeting / Smalltalk filter -> CHAT
    2. Fast Regex Boundary Pattern Weighting with Negative Penalties
    3. Consequential Safety Flagging
    4. Optional LLM Sub-Agent Micro-Router for ambiguous queries
    """
    start_time = time.perf_counter()
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()

    # Stage 1: Fast Smalltalk / Greeting check
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, msg_lower):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return RoutingResult(
                agent=AgentType.CHAT,
                confidence=0.95,
                latency_ms=round(elapsed_ms, 3),
                route_stage="fast_smalltalk_filter",
                scores={AgentType.CHAT.value: 1.0},
                is_consequential=False,
            )

    # Stage 2: Weighted Pattern Matching with Negative Suppression
    scores: Dict[AgentType, float] = {agent: 0.0 for agent in KEYWORD_RULES}
    matched: Dict[AgentType, List[str]] = {agent: [] for agent in KEYWORD_RULES}

    for agent, rules in KEYWORD_RULES.items():
        for pattern, weight in rules:
            if re.search(pattern, msg_lower):
                scores[agent] += weight
                matched[agent].append(pattern)

    # Apply Negative Penalties
    for agent, neg_rules in NEGATIVE_RULES.items():
        for pattern, penalty in neg_rules:
            if re.search(pattern, msg_lower):
                scores[agent] = max(0.0, scores[agent] - penalty)

    # Consequential Action Check
    consequential = is_consequential_action(msg_lower)

    # Find highest scoring agent
    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_score = sum(scores.values())

    confidence = round(best_score / total_score, 3) if total_score > 0 else 0.0

    # Decision Threshold
    if best_score >= 1.5:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.debug(f"Fast-path routed to {best_agent.value} (score={best_score}, conf={confidence}) in {elapsed_ms:.2f}ms")
        return RoutingResult(
            agent=best_agent,
            confidence=min(1.0, confidence),
            latency_ms=round(elapsed_ms, 3),
            route_stage="fast_pattern_scoring",
            scores={k.value: round(v, 2) for k, v in scores.items()},
            matched_keywords=matched[best_agent],
            is_consequential=consequential,
        )

    # Stage 3: LLM Sub-Agent Fallback if enabled and score is ambiguous
    if use_llm:
        try:
            llm_agent = await _llm_subagent_route(msg_clean)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return RoutingResult(
                agent=llm_agent,
                confidence=0.85,
                latency_ms=round(elapsed_ms, 3),
                route_stage="llm_subagent_router",
                scores={llm_agent.value: 1.0},
                is_consequential=consequential,
            )
        except Exception as e:
            logger.warning(f"LLM routing failed, falling back to default: {e}")

    # Stage 4: Default fallback
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return RoutingResult(
        agent=AgentType.CHAT,
        confidence=0.50 if best_score == 0 else 0.65,
        latency_ms=round(elapsed_ms, 3),
        route_stage="default_conversational_fallback",
        scores={k.value: round(v, 2) for k, v in scores.items()},
        is_consequential=consequential,
    )


async def _llm_route(message: str) -> AgentType:
    from app.ai.llm.prompt_manager import ROUTING_PROMPT
    from app.ai.llm.ollama_client import ollama_client
    from app.ai.llm.model_manager import model_manager
    
    messages = [{'role': 'system', 'content': ROUTING_PROMPT}, {'role': 'user', 'content': message}]
    
    # Use the ultra-fast 1B routing model
    target_model = model_manager.get_model('subagents.router')
    result = await ollama_client.chat(messages, model=target_model)
    result = result.strip().lower()
    
    try:
        return AgentType(result)
    except ValueError:
        return AgentType.CHAT
