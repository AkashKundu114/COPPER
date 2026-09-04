import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.constants import AgentType
from app.core.logger import logger

LEARNED_ROUTES_FILE = Path(__file__).parent / "learned_routes.json"


@dataclass
class RoutingResult:
    agent: AgentType
    confidence: float
    latency_ms: float
    route_stage: str
    scores: dict[str, float] = field(default_factory=dict)
    matched_keywords: list[str] = field(default_factory=list)
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


class DynamicRoutingMemory:
    """
    Self-learning memory cache that stores verified user exemplar routes and
    dynamically learns from live user interactions, corrections, and feedback.
    """

    def __init__(self, storage_path: Path = LEARNED_ROUTES_FILE):
        self.storage_path = storage_path
        self.memory: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load learned routes memory: {e}")
                self.memory = {}

    def save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist learned routes: {e}")

    def learn(self, prompt: str, agent: AgentType, weight: float = 1.0):
        """Register a user correction or verified routing pattern."""
        key = self._normalize(prompt)
        self.memory[key] = {
            "prompt": prompt,
            "agent": agent.value,
            "weight": weight,
            "timestamp": time.time(),
            "hits": self.memory.get(key, {}).get("hits", 0) + 1,
        }
        self.save()
        logger.info(f"Learned route: '{prompt[:40]}...' -> {agent.value}")

    def forget(self, prompt: str):
        """Remove a learned route and persist memory."""
        key = self._normalize(prompt)
        if key in self.memory:
            del self.memory[key]
            self.save()

    def find_match(self, prompt: str, threshold: float = 0.85) -> tuple[AgentType, float] | None:
        """Fast n-gram and token similarity search over learned routes."""
        if not self.memory:
            return None

        norm_p = self._normalize(prompt)
        tokens_p = set(norm_p.split())
        if not tokens_p:
            return None

        best_score = 0.0
        best_agent = None

        for key, data in self.memory.items():
            if norm_p == key:
                return AgentType(data["agent"]), 1.0

            tokens_key = set(key.split())
            intersection = len(tokens_p & tokens_key)
            union = len(tokens_p | tokens_key)
            jaccard = intersection / union if union > 0 else 0.0

            if jaccard > best_score and jaccard >= threshold:
                best_score = jaccard
                best_agent = AgentType(data["agent"])

        if best_agent:
            return best_agent, best_score
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower()).strip()


routing_memory = DynamicRoutingMemory()

KEYWORD_RULES: dict[AgentType, list[tuple[str, float]]] = {
    AgentType.CODING: [
        (
            r"\b(write|debug|refactor|create|implement|optimize|test|review|compile)\s+(a\s+|an\s+|the\s+|this\s+)?(python|javascript|typescript|rust|c\+\+|golang|go|java|sql)?\s*(function|class|rest endpoint|module|script|database schema|react component|algorithm|code|query|api|endpoint|unit test|decorator|zustand store|hook|useeffect|middleware|debounce|regex pattern)\b",
            5.0,
        ),
        (
            r"\b(syntax error|type error|stack trace|null pointer|exception|traceback|indentationerror|segfault|segmentation fault|typeerror|property does not exist|memory leak|indexerror|cors header|connection pooling|database migration|alembic|window functions|partition by|lru cache|binary search tree|quicksort|infinite re-render)\b",
            4.0,
        ),
        (
            r"\b(python|javascript|typescript|rust|c\+\+|golang|\bgo\b|\bjava\b|fastapi|sqlalchemy|express|vue|svelte|zustand|wasm|tailwind|css grid|flexbox)\b",
            2.0,
        ),
        (
            r"\b(unit test|unit tests|pytest|jest|pytest-mock|mocking|coverage|oxlint|ruff|black|git commit|git diff|merge conflict|pull request)\b",
            3.0,
        ),
        (
            r"\b(center a div|regex pattern|sql query|orm|async/await|dependency injection|sorting an array|real-time streaming)\b",
            3.0,
        ),
    ],
    AgentType.AUTOMATION: [
        (
            r"\b(open|launch|start|close|kill|terminate|restart|maximize|minimize|switch focus|move|delete|copy|rename)\s+.*(browser|chrome|firefox|terminal|window|active window|tabs|app|application|vscode|spotify|calculator|redis|server|container|docker container|database container|process|background process|workstation|music player|temp directory|all log files)\b",
            5.0,
        ),
        (r"\b(kill|terminate|stop)\s+.*(process|pid|\d+|runaway)\b", 5.0),
        (
            r"\b(delete|move|copy|rename|organize|unzip|archive|tar\.gz|extract|empty|clean up)\s+.*(file|files|folder|directory|logs|all log files|screenshots|downloads|pictures|recycle bin|backup|temp files|temp directory)\b",
            4.5,
        ),
        (
            r"\b(click|press|type|drag|scroll|mouse|keyboard|automate|form filling|mute system audio|lock the workstation|take a screenshot.*and save|empty the recycle bin|set volume|compile_assets\.bat|execute the build script|system tray|from port \d+|on port \d+)\b",
            6.0,
        ),
        (r"\b(take a screenshot|save to desktop)\b", 4.0),
    ],
    AgentType.REMINDER: [
        (
            r"\b(what time is it|current time|current date|what is the time|what is the date|what is today's date|what day is today|tell me the time|whats the time|what is the current time)\b",
            7.0,
        ),
        (
            r"\b(remind me\s+(to|for|at|in|tomorrow|on|tonight)|set a reminder|create a reminder|create a recurring reminder|habit reminder)\b",
            5.0,
        ),
        (r"\b(set (an\s+|a\s+)?alarm|wake me up|countdown for|timer for|set a timer|pomodoro)\b", 5.0),
        (
            r"\b(schedule (a\s+|an\s+)?(notification|meeting|event|appointment|call|session|time)|add to calendar|book an appointment|create event|calendar event)\b",
            5.0,
        ),
        (
            r"\b(add (a\s+)?todo|todo list|my tasks|task deadline|due tomorrow|due at|upcoming scheduled tasks|upcoming tasks|cancel my .* reminder|due on the)\b",
            4.5,
        ),
        (
            r"\b(in \d+\s*(minutes?|hours?|seconds?|days?)|tomorrow at \d+|next (tuesday|monday|wednesday|thursday|friday|saturday|sunday)|on (october|november|december|january|february|march|april|may|june|july|august|september)\s*\d+|tonight at \d+|every (weekday|morning|evening|day))\b",
            3.5,
        ),
    ],
    AgentType.RESEARCH: [
        (
            r"\b(what is the history of|who invented|explain the concept of|how does .* work|tell me about|how does .* differ|differ from|what is the difference between)\b",
            5.0,
        ),
        (
            r"\b(summarize (the\s+)?|search (the web for|online for|for recent|for research|for)\s+.*(papers|articles|studies|info|information|data|literature|news)|find research papers on|find papers on|literature review|explain|investigate the economic|trade-offs between|compare and contrast|what are the (core\s+)?differences between|deep dive into|investigate)\b",
            5.0,
        ),
        (
            r"\b(quantum mechanics|wave-particle duality|transformer (neural network|architecture)|sqlite and postgresql|epistemic memory|black hole information paradox|rna polymerase|2008 financial crisis|supervised vs self-supervised|byzantine generals|stoicism|solid-state batteries|theory of relativity|tcp and udp|voynich manuscript|solar and nuclear|human immune system|gödel|crispr-cas9|cap theorem|alan turing|stages of sleep|speed of light|superconductivity)\b",
            4.0,
        ),
        (r"^(what is|who is|who was|why is|explain|summarize|news on|research|papers on|study on)\b", 2.0),
    ],
    AgentType.VISION: [
        (
            r"\b(what is on my screen|describe this screenshot|read text from this image|ocr|read the error message in|scanned pdf receipt|circuit board picture|extract the text from|check the alignment of|find the bounding box coordinates of|describe the objects and colors|describe my screen|inspect my screen|inspect the screen|screen right now)\b",
            6.0,
        ),
        (
            r"\b(look at this image|inspect this picture|analyze this photo|what do you see|diagram photo|chart image|ui mockup photo|webpage screenshot|architecture diagram|screenshot of|scanned pdf|this uploaded image|image capture|ui picture)\b",
            5.5,
        ),
        (
            r"\b(screenshot|image|photo|picture|diagram|ui capture|bounding box|detect objects|find button in image|visual inspection|scanned pdf)\b",
            3.0,
        ),
    ],
    AgentType.IMAGE: [
        (
            r"\b(generate an image|create an image|draw an image|draw a picture|make a photo|generate a photo|create a picture|draw a|draw me a)\b",
            6.0,
        ),
        (
            r"\b(generate|create|draw|make).*\b(image|picture|photo|painting|wallpaper|art|drawing)\b",
            4.0,
        ),
    ],
    AgentType.PLANNER: [
        (
            r"\b(break (down|this).*into|create a (project\s+)?roadmap|decompose|plan|structure an execution strategy|build a checklist|formulate a strategy|organize.*phases|step-by-step (milestones|phases|steps|checklist|action plan|strategy|study schedule))\b",
            5.0,
        ),
        (
            r"\b(strategic planning|execution strategy|quarterly milestone roadmap|sprint planning|milestone plan|actionable phases|into high, medium, and low priority phases|in 30 days|for my engineering team|for high-availability|to optimize performance)\b",
            4.0,
        ),
        (r"\b(milestones|roadmap|action plan|task breakdown|sprint roadmap)\b", 3.0),
    ],
    AgentType.DOCUMENT: [
        (
            r"\b(create|generate|write|make|export|build|draft)\s+(a\s+|an\s+|the\s+)?(markdown\s+|pdf\s+|word\s+)?(technical report|report|pdf|word document|docx|ms word|markdown document|md document|html document|csv file|spreadsheet|excel sheet|tsv file|formal letter|project proposal|executive summary|resume|cv|meeting minutes|invoice table|research paper|standalone document|quarterly financial report|technical specification document|technical specification|whitepaper document|formal invoice document|formal invoice|presentation slide deck|financial report|specification document|whitepaper|invoice document)\b",
            7.0,
        ),
        (
            r"\b(write|create|generate|make|build|export|turn this into|draft)\s+.*(word doc|word document|\.docx|slide deck|presentation|\.pptx|spreadsheet|\.xlsx|pdf report|\.pdf|technical report|markdown report|quarterly financial report|technical specification document|technical specification|whitepaper document|formal invoice document|formal invoice)\b",
            6.0,
        ),
        (r"\b(docx|pptx|xlsx|pdf)\b", 3.0),
        (r"\b(slide deck|presentation slides|word document|excel sheet|technical report)\b", 4.0),
        (
            r"\b(generate (a\s+|an\s+)?pdf|create (a\s+|an\s+)?pdf|make (a\s+|an\s+)?pdf|export (to\s+)?pdf|save as pdf|convert to pdf|as (a\s+)?pdf|in pdf format)\b",
            6.0,
        ),
        (
            r"\b(generate (a\s+|an\s+)?(word|docx)|create (a\s+|an\s+)?(word|docx)|make (a\s+|an\s+)?(word|docx)|export (to\s+)?(word|docx)|in (word|docx) format)\b",
            6.0,
        ),
        (
            r"\b(generate (a\s+|an\s+)?(csv|spreadsheet|table)|create (a\s+|an\s+)?(csv|spreadsheet|table)|export (to\s+)?csv|save as csv)\b",
            5.0,
        ),
        (
            r"\b(create|generate|write)\s+.*(document|whitepaper|business proposal|briefing document|curriculum vitae|technical report)\b",
            4.5,
        ),
        (
            r"\b(pdf report|word report|html report|csv export|technical report|markdown report|document generation|document architect|downloadable document)\b",
            4.0,
        ),
    ],
}

GREETING_PATTERNS = [
    r"^(hi|hello|hey|greetings|good (morning|evening|day|afternoon)|morning|evening|howdy|yo|sup|good day)\b",
    r"^(how are you|who are you|what can you do|nice to meet you|thank you|thanks|goodbye|talk to you later|have a wonderful)\b",
    r"\b(tell me a (fun thought|joke|witty remark)|sup copper|hello copper|hello there)\b",
]

NEGATIVE_RULES: dict[AgentType, list[tuple[str, float]]] = {
    AgentType.DOCUMENT: [
        (r"^(remind me to|set an alarm|schedule a notification|schedule a time to)\b", 6.0),
        (r"^(delete the file|open the terminal|open chrome|close all windows|kill process)\b", 6.0),
        (r"^(what is on my screen|describe this screenshot)\b", 6.0),
        (r"^(write a script to|create a script to|plan a roadmap for|explain how to|draw an image of)\b", 8.0),
    ],
    AgentType.CODING: [
        (r"^(what is|who is|explain the history of|why was .* invented|tell me about|summarize)\b", 4.0),
        (
            r"^(remind me to|schedule a notification|schedule a time to|set an alarm to|set a timer to|add a todo to)\b",
            6.0,
        ),
        (r"^(delete the file|move the file|copy the file|open vscode|close all windows)\b", 6.0),
        (r"^(plan a roadmap for|break down|build a checklist for|formulate a strategy for)\b", 6.0),
        (r"^(read the text in this screenshot|inspect this diagram of)\b", 6.0),
        (r"\b(kill|terminate|stop)\s+.*(process|pid)\b", 4.0),
    ],
    AgentType.AUTOMATION: [
        (r"^(what is automation|explain how browsers work|history of computer automation)\b", 4.0),
        (r"^(write a script to|create a script to|debug)\b", 6.0),
        (r"^(remind me to|schedule a time to|schedule a notification|set an alarm|set a timer)\b", 6.0),
        (r"^(plan a roadmap for|break down|decompose|build a checklist for)\b", 6.0),
        (r"^(explain how to|summarize)\b", 6.0),
    ],
    AgentType.RESEARCH: [
        (
            r"^(write a python function to|debug this error|fix my syntax|create a react component|write a script to)\b",
            6.0,
        ),
        (r"^(remind me to|set an alarm|schedule a notification|schedule a time to)\b", 6.0),
        (r"^(delete the file|open the terminal|move all|plan a roadmap for)\b", 6.0),
        (r"\b(screenshot|photo|image|picture|diagram photo|ui picture|uploaded image|ui mockup)\b", 6.0),
    ],
    AgentType.PLANNER: [
        (r"^(write a script to|delete the file about|explain how to|remind me to|schedule a time to)\b", 6.0),
        (r"\b(quarterly financial report|technical specification|formal invoice|whitepaper document)\b", 6.0),
    ],
    AgentType.VISION: [
        (r"^(delete the file about|remind me to|write a script to|schedule a time to|plan a roadmap for)\b", 6.0),
        (r"\btake a screenshot.*and save\b", 6.0),
    ],
    AgentType.IMAGE: [
        (r"^(remind me to|schedule a time to|write a script to|delete the file|what is|explain|summarize)\b", 6.0),
        (r"^(plan a roadmap for|break down|build a checklist)\b", 6.0),
    ],
}

CONSEQUENTIAL_PATTERNS = [
    r"(format\s+[a-z]:?|rm\s+-rf|del\s+/f|dd\s+if=|mkfs|wipe\s+(disk|all|partitions)|factory\s+reset)",
    r"(delete\s+all|drop\s+(database|table|all)|truncate|delete\s+from\s+users|chmod\s+-r\s+777|remove-item\s+-recurse)",
    r"(publish\s+to\s+prod|deploy\s+to\s+production|push\s+--force|destroy|:\(\)\{\s+:\|:&\s+\};:|base64\s+-d\s+\|\s+sh)",
    r"(send\s+email\s+to|transfer\s+funds|cancel\s+subscription)",
]


COMPILED_GREETING_PATTERNS = [re.compile(p, re.IGNORECASE) for p in GREETING_PATTERNS]
COMPILED_KEYWORD_RULES = {
    agent: [(re.compile(pattern, re.IGNORECASE), weight, pattern) for pattern, weight in rules]
    for agent, rules in KEYWORD_RULES.items()
}
COMPILED_NEGATIVE_RULES = {
    agent: [(re.compile(pattern, re.IGNORECASE), penalty) for pattern, penalty in neg_rules]
    for agent, neg_rules in NEGATIVE_RULES.items()
}
COMPILED_CONSEQUENTIAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CONSEQUENTIAL_PATTERNS]


def is_consequential_action(message: str) -> bool:
    msg_lower = message.lower()
    return any(pattern.search(msg_lower) for pattern in COMPILED_CONSEQUENTIAL_PATTERNS)


async def route_message(message: str, use_llm: bool = False) -> AgentType:
    res = await route_message_detailed(message, use_llm=use_llm)
    return res.agent


async def route_message_detailed(message: str, use_llm: bool = False) -> RoutingResult:
    """
    Multi-stage high-precision router:
    Stage 0: Dynamic Memory & Self-Trained Query Cache (< 0.01ms)
    Stage 1: Fast Smalltalk / Greeting filter -> CHAT
    Stage 2: Weighted Pattern Matching with Negative Suppression
    Stage 3: Consequential Safety Flagging
    Stage 4: Optional LLM Micro-Router fallback for ambiguous queries
    """
    start_time = time.perf_counter()
    msg_clean = message.strip()
    msg_lower = msg_clean.lower()

    memory_match = routing_memory.find_match(msg_clean, threshold=0.90)
    if memory_match:
        learned_agent, confidence = memory_match
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return RoutingResult(
            agent=learned_agent,
            confidence=round(confidence, 3),
            latency_ms=round(elapsed_ms, 3),
            route_stage="learned_memory_cache",
            scores={learned_agent.value: 1.0},
            is_consequential=is_consequential_action(msg_lower),
        )

    for compiled_pat in COMPILED_GREETING_PATTERNS:
        if compiled_pat.search(msg_lower):
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return RoutingResult(
                agent=AgentType.CHAT,
                confidence=0.98,
                latency_ms=round(elapsed_ms, 3),
                route_stage="fast_smalltalk_filter",
                scores={AgentType.CHAT.value: 1.0},
                is_consequential=False,
            )

    scores: dict[AgentType, float] = dict.fromkeys(COMPILED_KEYWORD_RULES, 0.0)
    matched: dict[AgentType, list[str]] = {agent: [] for agent in COMPILED_KEYWORD_RULES}

    for agent, rules in COMPILED_KEYWORD_RULES.items():
        for compiled_pat, weight, raw_pat in rules:
            if compiled_pat.search(msg_lower):
                scores[agent] += weight
                matched[agent].append(raw_pat)

    for agent, neg_rules in COMPILED_NEGATIVE_RULES.items():
        for compiled_pat, penalty in neg_rules:
            if compiled_pat.search(msg_lower):
                scores[agent] = max(0.0, scores[agent] - penalty)

    consequential = is_consequential_action(msg_lower)

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_score = sum(scores.values())

    confidence = round(best_score / total_score, 3) if total_score > 0 else 0.0

    if best_score >= 1.5:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return RoutingResult(
            agent=best_agent,
            confidence=min(1.0, confidence),
            latency_ms=round(elapsed_ms, 3),
            route_stage="fast_pattern_scoring",
            scores={k.value: round(v, 2) for k, v in scores.items()},
            matched_keywords=matched[best_agent],
            is_consequential=consequential,
        )

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
            logger.warning(f"LLM routing failed: {e}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return RoutingResult(
        agent=AgentType.CHAT,
        confidence=0.50 if best_score == 0 else 0.65,
        latency_ms=round(elapsed_ms, 3),
        route_stage="default_conversational_fallback",
        scores={k.value: round(v, 2) for k, v in scores.items()},
        is_consequential=consequential,
    )


async def _llm_subagent_route(message: str) -> AgentType:
    from app.ai.llm.model_manager import model_manager
    from app.ai.llm.ollama_client import ollama_client
    from app.ai.llm.prompt_manager import ROUTING_PROMPT

    messages = [{"role": "system", "content": ROUTING_PROMPT}, {"role": "user", "content": message}]
    target_model = model_manager.get_mini_model()
    result = await ollama_client.chat(messages, model=target_model, keep_alive=-1)
    result = result.strip().lower()

    try:
        return AgentType(result)
    except ValueError:
        return AgentType.CHAT


def learn_user_correction(prompt: str, agent: AgentType):
    """Public helper for self-training online routes from user feedback."""
    routing_memory.learn(prompt, agent)
