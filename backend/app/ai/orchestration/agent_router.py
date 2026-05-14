from app.core.constants import AgentType
from app.core.logger import logger


KEYWORD_MAP = {
    AgentType.CODING: [
        "code", "function", "bug", "debug", "error", "python", "javascript",
        "typescript", "class", "import", "compile", "script", "program", "git",
        "refactor", "test", "unit test", "api", "endpoint", "algorithm",
    ],
    AgentType.AUTOMATION: [
        "open", "launch", "click", "type", "automate", "run", "execute",
        "screenshot", "window", "desktop", "browser", "file", "folder",
        "copy", "move", "delete", "rename", "organize",
    ],
    AgentType.REMINDER: [
        "remind", "reminder", "schedule", "alarm", "todo", "task",
        "deadline", "meeting", "appointment", "at ", "tomorrow", "tonight",
        "next week", "every day", "daily", "weekly", "monthly",
    ],
    AgentType.RESEARCH: [
        "research", "search", "find out", "explain", "summarize", "compare",
        "what is", "who is", "how does", "why does", "analyze", "investigate",
        "report on", "details about",
    ],
    AgentType.VISION: [
        "screenshot", "image", "picture", "photo", "ocr", "extract text",
        "what do you see", "analyze this image", "read this", "scan",
        "what's on screen", "look at",
    ],
}


async def route_message(message: str, use_llm: bool = False) -> AgentType:
    """Route message to appropriate agent using keyword matching or LLM."""
    msg_lower = message.lower()

    # Keyword-based routing (fast)
    scores = {agent: 0 for agent in AgentType}
    for agent, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[agent] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        logger.debug(f"Routing to {best} (score={scores[best]})")
        return best

    # LLM-based routing (fallback)
    if use_llm:
        try:
            return await _llm_route(message)
        except Exception as e:
            logger.warning(f"LLM routing failed: {e}")

    return AgentType.CHAT


async def _llm_route(message: str) -> AgentType:
    from app.ai.llm.prompt_manager import ROUTING_PROMPT
    from app.ai.llm.ollama_client import ollama_client

    messages = [
        {"role": "system", "content": ROUTING_PROMPT},
        {"role": "user", "content": message},
    ]
    result = await ollama_client.chat(messages)
    result = result.strip().lower()
    try:
        return AgentType(result)
    except ValueError:
        return AgentType.CHAT
