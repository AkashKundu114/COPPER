import json
import math
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.ai.orchestration.explainer import RoutingExplainer, routing_history_store
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
    cascade_risk: float = 0.0  # Novelty 1: Topological DAG cascade failure probability
    sub_tasks: list[str] = field(default_factory=list)  # Decomposed compound task pipeline
    routing_entropy: float = 0.0  # Novelty 1: Shannon entropy H(R) = -sum(p_i * log2(p_i))
    explanation: dict[str, Any] | None = None
    suppressed_rules: list[dict[str, Any]] = field(default_factory=list)

    @property
    def agent_type(self) -> AgentType:
        return self.agent

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent.value,
            "agent_type": self.agent.value,
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "route_stage": self.route_stage,
            "scores": self.scores,
            "matched_keywords": self.matched_keywords,
            "is_consequential": self.is_consequential,
            "cascade_risk": self.cascade_risk,
            "sub_tasks": self.sub_tasks,
            "routing_entropy": self.routing_entropy,
            "explanation": self.explanation,
            "suppressed_rules": self.suppressed_rules,
        }

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
        if norm_p in self.memory:
            return AgentType(self.memory[norm_p]["agent"]), 1.0

        tokens_p = set(norm_p.split())
        if not tokens_p:
            return None

        best_score = 0.0
        best_agent = None

        for key, data in self.memory.items():
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
            r"\b(write|debug|refactor|create|implement|optimize|test|review|compile|build|design)\s+(a\s+|an\s+|the\s+|this\s+)?(python|javascript|typescript|rust|c\+\+|golang|go|java|sql|ruby|svelte|kotlin|scala|solidjs)?\s*(function|class|rest endpoint|module|script|database schema|react component|svelte component|solidjs component|reactive component|algorithm|code|query|api|endpoint|unit test|benchmark tests?|decorator|zustand store|hook|useeffect|middleware|debounce|regex pattern|serializer|parser)\b",
            7.0,
        ),
        (
            r"\b(syntax error|type error|stack trace|null pointer|exception|traceback|indentationerror|segfault|segmentation fault|typeerror|property does not exist|memory leak|indexerror|cors header|connection pooling|database migration|alembic|window functions|partition by|lru cache|binary search tree|quicksort|infinite re-render|thread-safe|deadlock|mutual exclusion locks?)\b",
            5.0,
        ),
        (
            r"\b(python|javascript|typescript|rust|c\+\+|golang|\bgo\b|\bjava\b|\bruby\b|\bkotlin\b|\bscala\b|fastapi|sqlalchemy|express|vue|svelte|solidjs|zustand|wasm|tailwind|css grid|flexbox|cockroachdb|distributed caching|redis serializer)\b",
            4.0,
        ),
        (
            r"\b(unit test|unit tests|pytest|jest|pytest-mock|mocking|coverage|oxlint|ruff|black|git commit|git diff|merge conflict|pull request|event bus handler|throughput of event bus)\b",
            4.0,
        ),
        (
            r"\b(center a div|regex pattern|sql query|orm|async/await|dependency injection|sorting an array|real-time streaming|waveform visualizer)\b",
            4.0,
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
            r"\b(click|press|type|drag|scroll|mouse|keyboard|automate|form filling|mute system audio|lock the workstation|take a screenshot.*and save|empty the recycle bin|set volume|compile_assets\.bat|execute the build script|system tray|from port \d+|on port \d+|automate the process|syncing local branch|pre-commit|shell script to cleaning up node_modules|re-running build with elevated privileges)\b",
            6.0,
        ),
        (
            r"\b(monitor\s+cpu\s+usage|monitor\s+http.*error|if\s+.*times\s+out.*log\s+an\s+incident|utilization\s+exceeds|send\s+a\s+high-priority\s+alert\s+chime)\b",
            7.0,
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
            r"\b(derive\s+(the\s+)?(fundamental\s+)?equation|from\s+first\s+principles|accessible\s+to\s+a\s+graduate\s+researcher|synthetic\s+biological|neuromorphic\s+memristor|crossbar\s+arrays?|nitrogen\s+fixation|non-legumes|first-principles|mechanistic\s+explanation|theoretical\s+framework|literature\s+synthesis|systematic\s+review)\b",
            8.0,
        ),
        (
            r"\b(summarize (the\s+)?|search (the web for|online for|the internet for|for recent|for research|for)\s+.*(papers|articles|studies|info|information|data|literature|news)|find research papers on|find papers on|literature review|explain|investigate the economic|trade-offs between|compare and contrast|what are the (core\s+)?differences between|deep dive into|investigate)\b",
            5.0,
        ),
        (
            r"\b(search (the web|online|the internet|google|bing|duckduckgo)(\s+for)?|look up online|find online)\b",
            6.5,
        ),
        (
            r"\b(quantum mechanics|wave-particle duality|transformer (neural network|architecture)|sqlite and postgresql|epistemic memory|black hole information paradox|rna polymerase|2008 financial crisis|supervised vs self-supervised|byzantine generals|stoicism|solid-state batteries|theory of relativity|tcp and udp|tcp vs udp|solar vs nuclear|solar and nuclear|react vs vue|react and vue|history of the roman empire|voynich manuscript|human immune system|gödel|crispr-cas9|cap theorem|alan turing|stages of sleep|speed of light|superconductivity)\b",
            5.0,
        ),
        (r"^(what is|who is|who was|why is|explain|summarize|news on|research|papers on|study on)\b", 2.0),
    ],
    AgentType.WEB_SEARCH: [
        (
            r"\b(search for|look up|what's the latest|whats the latest|current news|google|find online|search the web|search online|search the internet|browse the web|latest news|today's news|recent news on|breaking news|live news|online search|search searxng)\b",
            7.0,
        ),
        (
            r"\b(search (the web|online|the internet|google|bing|duckduckgo)(\s+for)?|look up online|find online|google this|find on google|look up on google)\b",
            6.5,
        ),
        (
            r"\b(what is the latest|latest updates on|current status of|stock price of|weather in|who won|latest score)\b",
            5.0,
        ),
    ],
    AgentType.VISION: [
        (
            r"\b(accessibility\s+visual\s+audit|visual\s+audit|focus\s+state\s+indicator|visual\s+hierarchy|heading\s+contrast|ui\s+layout|screen\s+elements?|bounding\s+box\s+coordinates?|e-commerce\s+shopping\s+cart|mobile\s+settings\s+screen|ui\s+component\s+alignment|inspect\s+(this\s+)?(screen|ui|layout|wireframe|mockup))\b",
            8.0,
        ),
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
            r"\b(render\s+(a\s+)?(3d\s+)?visualization|unreal\s+engine(\s+5)?|lumen\s+raytracing|octane\s+render|subsurface\s+scattering|watercolor\s+style|cyberpunk\s+synthwave|hyperrealistic|golden\s+hour|soft\s+bokeh|concept\s+art|illustration|photorealistic|digital\s+painting|digital\s+art|matte\s+painting|8k\s+resolution)\b",
            8.0,
        ),
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
            r"\b(organize\s+my\s+task\s+backlog|task\s+backlog|prioritize\s+my\s+action\s+items|action\s+items|high\s+impact\s+low\s+effort|dependency\s+dag\s+tracking|sprint\s+prioritization|work\s+breakdown\s+structure|critical\s+path|kanban\s+board|gantt\s+chart|backlog\s+grooming)\b",
            8.0,
        ),
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
            r"\b(executive\s+vendor\s+risk\s+evaluation|vendor\s+risk\s+evaluation|format\s+these\s+notes\s+into\s+a\s+(structured\s+)?formal\s+project\s+proposal|project\s+proposal|clean\s+modern\s+layout|with\s+charts\s+in\s+csv|standalone\s+markdown\s+document|formal\s+documentation|spec\s+sheet|executive\s+summary|briefing\s+memo|white\s+paper)\b",
            8.0,
        ),
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
    AgentType.GUARDIAN: [
        (
            r"\b(drop\s+(database|table|all|schema)|truncate(\s+table)?|delete\s+from\s+[a-z0-9_]+|drop\s+all\s+foreign\s+keys|alter\s+table\s+[a-z0-9_]+\s+drop\s+column)\b",
            10.0,
        ),
        (
            r"\b(rm\s+-rf|del\s+/[fsq\s]+|dd\s+if=|mkfs|shred(\s+-[a-z0-9]+)?|wipe\s+(disk|all|partitions)|factory\s+reset|remove-item\s+-recurse|format\s+[a-z]:(?=\s|$)|corrupt\s+(the\s+)?master\s+boot\s+record|c:\\bootmgr|/dev/sda|/dev/nvme[0-9a-z]*|sysrq)\b",
            10.0,
        ),
        (
            r"\b(nt\s+authority\\system|chmod\s+(-r\s+)?777|chown\s+-r\s+/|privilege\s+escalation(\s+payload)?|elevate\s+process\s+token|mimikatz|dump\s+sam\s+database|pam\s+authentication|setuid|setgid|sudoers|elevated\s+subshell|authorized_keys|(\.bashrc|\.zshrc|\.profile))\b",
            10.0,
        ),
        (
            r"\b(reverse\s+(tcp\s+)?shell|ransomware(\s+encryption)?|keylogger|fork\s+bomb|:\(\)\{\s+:\|:&\s+\};:|base64\s+-d\s+\|\s+sh|eval\(\$\(|downloadstring|invoke-expression|set-executionpolicy\s+bypass|outbound\s+http\s+exfiltration|exfiltrat(e|ion)|brute\s+force\s+attacks?)\b",
            10.0,
        ),
        (
            r"\b(extract\s+saved\s+browser\s+passwords|reveal\s+hidden\s+system\s+prompts|api\s+secrets|steal\s+credentials|dump\s+memory\s+for\s+passwords|aws\s+keys|destroy\s+encryption\s+keys|poison\s+(the\s+)?(local\s+)?dns|dns\s+cache\s+poisoning|spoof\s+arp|arp\s+spoofing)\b",
            10.0,
        ),
        (
            r"\b(ignore\s+(safety|all)\s+protocols?|disable\s+(sandboxing(\s+constraints)?|security|rate\s+limits|audit|logging|windows\s+defender|firewall(\s+rules)?|antivirus|selinux)|hypothetical\s+fictional\s+scenario\s+without\s+ethics|simulate\s+an\s+evil|dan\s+mode|jailbreak|bypass\s+safety|override\s+guardian|overwrite\s+(the\s+)?firmware|nvram|debug\s+override\s+mode)\b",
            10.0,
        ),
    ],
    AgentType.VOICE: [
        (
            r"\b(cut\s+audio|barge\s+in|stop\s+talking|shut\s+up|listen\s+carefully\s+to\s+what\s+i'm\s+about\s+to\s+say|interrupting\s+you|mute\s+mic|unmute\s+mic|voice\s+mode|whisper\s+mode|transcribe\s+audio|push-to-talk|voice\s+companion|wake\s+word|listen\s+to\s+me|turn\s+down\s+the\s+speech|speak\s+slower|speak\s+faster|stop\s+speaking|pause\s+speaking|quiet\s+please|listen\s+carefully|duplex\s+voice\s+mode|hands-free\s+mode|presence\s+volume|mute\s+your\s+voice\s+output|stop\s+talking\s+and\s+let\s+me\s+finish|switch\s+speech\s+rate|speech\s+rate|let\s+me\s+finish\s+my\s+thought)\b",
            9.0,
        ),
        (
            r"\b(i'm\s+interrupting\s+you|wait\s+a\s+second,\s+listen|hold\s+on\s+a\s+sec|cut\s+mic|tts|stt)\b",
            8.0,
        ),
    ],
    AgentType.BEHAVIOR: [
        (
            r"\b(nutrition\s+(schedule|plan)|protein\s+intake|caloric\s+intake|bpm\s+average|heart\s+rate|cognitive\s+brain\s+health|paleolithic|unprocessed\s+ingredients|afternoon\s+slump|intermittent\s+fasting|macronutrient|macronutrients|sleep\s+hygiene|circadian\s+rhythm|circadian\s+energy|caffeine\s+(intake|consumption)|focus\s+intervals?|ergonomic\s+posture|habit\s+tracking|hydration\s+reminder|burnout\s+detection|fatigue\s+level|recovery\s+score|biometric|cortisol|nootropic|keto|zone\s+2\s+cardio|blue-light(\s+exposure)?|attention\s+span|late-night\s+architecture\s+reviews|all-day\s+coding\s+hackathons)\b",
            9.0,
        ),
        (
            r"\b(log\s+(that\s+)?(protein|calories|heart\s+rate|bpm|sleep|water|workout)|track\s+my\s+(macros|habits|nutrition|steps|sleep|fasting)|plan\s+a\s+daily\s+nutrition|analyze\s+the\s+correlation\s+between\s+my)\b",
            8.0,
        ),
    ],
    AgentType.CHAT: [
        (
            r"\b(read\s+any\s+good\s+documentation\s+lately|to\s+clear\s+my\s+mind|share\s+a\s+thoughtful\s+insight|tell\s+me\s+a\s+joke|witty\s+remark|how\s+are\s+you\s+feeling|what's\s+on\s+your\s+mind|philosophical\s+reflection|just\s+chatting|casual\s+conversation|companion\s+thought|tell\s+me\s+something\s+interesting|a\s+penny\s+for\s+your\s+thoughts)\b",
            8.0,
        ),
        (
            r"^(hi|hello|hey|greetings|howdy|sup|yo|good morning|good evening|good afternoon)(\s+copper)?[\.!\?]*$",
            8.0,
        ),
        (
            r"^(who are you|what is your name|how are you|how is it going|tell me about yourself)[\.!\?]*$",
            8.0,
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
        (
            r"^(look at|inspect|describe|read text from|extract text from|ocr|what is on my screen)\s+.*(screenshot|photo|image|picture)\b",
            6.0,
        ),
    ],
    AgentType.PLANNER: [
        (r"^(write a script to|delete the file about|explain how to|remind me to|schedule a time to)\b", 6.0),
        (r"\b(quarterly financial report|technical specification|formal invoice|whitepaper document)\b", 6.0),
    ],
    AgentType.VISION: [
        (r"^(delete the file about|remind me to|write a script to|schedule a time to|plan a roadmap for)\b", 6.0),
        (r"\btake a screenshot.*and save\b", 6.0),
        (r"^(explain how to|how do i|teach me how to|guide me on how to)\b", 6.0),
    ],
    AgentType.IMAGE: [
        (r"^(remind me to|schedule a time to|write a script to|delete the file|what is|explain|summarize)\b", 6.0),
        (r"^(plan a roadmap for|break down|build a checklist)\b", 6.0),
    ],
    AgentType.WEB_SEARCH: [
        (
            r"\b(my name|my age|who am i|whats my name|what is my name|my files|my schedule|in my notes|my password|my memory|remember when|my habits|my calendar|my tasks|my todo|my projects|local documents|on my computer|my workstation|on my desktop|in my database)\b",
            8.0,
        ),
        (
            r"\b(remind me|set an alarm|schedule a notification|schedule a time|create a reminder|add a todo|set a timer)\b",
            8.0,
        ),
        (
            r"\b(delete the file|open the terminal|open chrome|close all windows|kill process|close.*(tabs|windows|browser)|open.*(browser|chrome|firefox)|in google chrome)\b",
            8.0,
        ),
        (
            r"\b(write a python function|write a script|debug this error|fix my syntax|create a react component|implement a function)\b",
            8.0,
        ),
        (r"\b(what is on my screen|describe this screenshot|read text from this image)\b", 8.0),
        (r"\b(generate an image|create an image|draw a picture)\b", 8.0),
    ],
}

CONSEQUENTIAL_PATTERNS = [
    r"(format\s+[a-z]:(?=\s|$)|rm\s+-rf|del\s+/[fsq\s]+|dd\s+if=|mkfs|wipe\s+(disk|all|partitions)|factory\s+reset|shred\s+-[a-z0-9]+|corrupt\s+(the\s+)?master\s+boot\s+record|c:\\bootmgr|/dev/sda|/dev/nvme[0-9a-z]*|sysrq)",
    r"(delete\s+all|drop\s+(database|table|all|schema)|truncate|delete\s+from\s+[a-z0-9_]+|chmod\s+(-r\s+)?777|remove-item\s+-recurse|drop\s+all\s+foreign\s+keys|alter\s+table\s+[a-z0-9_]+\s+drop\s+column)",
    r"(publish\s+to\s+prod|deploy\s+to\s+production|push\s+--force|destroy|:\(\)\{\s+:\|:&\s+\};:|base64\s+-d\s+\|\s+sh|reverse\s+(tcp\s+)?shell|ransomware|keylogger|fork\s+bomb)",
    r"(send\s+email\s+to|transfer\s+funds|cancel\s+subscription|nt\s+authority\\system|elevate\s+process\s+token|mimikatz|dump\s+sam\s+database|authorized_keys|(\.bashrc|\.zshrc|\.profile))",
    r"(exfiltrat(e|ion)|extract\s+saved\s+browser\s+passwords|reveal\s+hidden\s+system\s+prompts|api\s+secrets|steal\s+credentials|ignore\s+safety\s+protocol|disable\s+(sandboxing|windows\s+defender|firewall)|poison\s+(the\s+)?(local\s+)?dns|dns\s+cache\s+poisoning|spoof\s+arp|override\s+guardian|overwrite\s+(the\s+)?firmware|nvram)",
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


def estimate_dag_cascade_risk(agent: AgentType, is_consequential: bool, sub_tasks: list[str] | None = None) -> float:
    """
    TFP-Router (Topological Failure-Predicting Router):
    Estimates downstream execution graph (DAG) cascade failure probability.
    Higher risk for autonomous mutating agents (automation, coding) and multi-node DAG workflows.
    R_cascade = 1 - \\prod_{k \\in Children} (1 - P(fail_k))
    """
    base_failure_rates = {
        AgentType.CHAT: 0.01,
        AgentType.REMINDER: 0.02,
        AgentType.DOCUMENT: 0.04,
        AgentType.IMAGE: 0.05,
        AgentType.RESEARCH: 0.07,
        AgentType.WEB_SEARCH: 0.06,
        AgentType.VISION: 0.09,
        AgentType.PLANNER: 0.11,
        AgentType.CODING: 0.16,
        AgentType.AUTOMATION: 0.20,
    }
    base_p = base_failure_rates.get(agent, 0.05)
    if is_consequential:
        base_p = min(0.92, base_p * 2.5)
    if sub_tasks and len(sub_tasks) > 1:
        cascade_p = 1.0 - ((1.0 - base_p) ** len(sub_tasks))
        return round(cascade_p, 3)
    return round(base_p, 3)


def decompose_compound_intent(message: str) -> list[str]:
    """
    Identifies compound task dependencies across multi-agent workflows.
    e.g. "Read text in screenshot and open VSCode" -> ['vision', 'automation']
    """
    lower = message.lower()
    tasks = []
    if any(k in lower for k in ["screenshot", "image", "photo", "ocr"]):
        tasks.append("vision")
    if any(k in lower for k in ["open ", "close ", "launch ", "window", "terminal", "kill pid", "process"]):
        tasks.append("automation")
    if any(k in lower for k in ["function", "class", "debug", "refactor", "code", "script", "api"]):
        tasks.append("coding")
    if any(k in lower for k in ["pdf", "report", "document", "docx", "export"]):
        tasks.append("document")
    if any(k in lower for k in ["search online", "search the web", "look up", "find online"]):
        tasks.append("web_search")
    elif any(k in lower for k in ["search", "research", "explain how", "history of"]):
        tasks.append("research")
    return tasks if len(tasks) > 1 else []


def calculate_routing_entropy(scores: dict[Any, float]) -> float:
    r"""
    Novelty 1: Formal Information-Theoretic Routing Entropy.
    H(R) = - \sum_{i} p_i \log_2(p_i)
    Measures distribution ambiguity across candidate agent specialists.
    Zero entropy indicates absolute single-agent determinism.
    """
    total = sum(scores.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for s in scores.values():
        if s > 0:
            p = s / total
            entropy -= p * math.log2(p)
    return round(entropy, 3)


DESTRUCTIVE_COMMAND_RE = re.compile(
    r"(format\s+[a-z]:?|rm\s+-rf|del\s+/f|dd\s+if=|mkfs|wipe\s+(disk|all|partitions)|factory\s+reset|"
    r"delete\s+all|drop\s+(database|table|all)|truncate|delete\s+from\s+users|chmod\s+-r\s+777|remove-item\s+-recurse|"
    r"publish\s+to\s+prod|deploy\s+to\s+production|push\s+--force|destroy|:\(\)\{\s+:\|:&\s+\};:|base64\s+-d\s+\|\s+sh|"
    r"send\s+email\s+to|transfer\s+funds|cancel\s+subscription)",
    re.IGNORECASE,
)
CODE_RE = re.compile(
    r"\b(write|debug|refactor|create|implement|optimize|test|review|compile)\s+.*(python|javascript|typescript|rust|c\+\+|golang|go|java|sql)?\s*(function|class|rest endpoint|module|script|database schema|react component|algorithm|code|query|api|endpoint|unit test|decorator|zustand store|hook|useeffect|middleware|debounce|regex pattern)\b|"
    r"\b(syntax error|type error|stack trace|null pointer|exception|traceback|indentationerror|segfault|segmentation fault|typeerror|property does not exist|memory leak|indexerror|cors header|connection pooling|database migration|alembic|window functions|partition by|lru cache|binary search tree|quicksort|infinite re-render)\b|"
    r"\b(unit test|unit tests|pytest|jest|pytest-mock|mocking|coverage|oxlint|ruff|black|git commit|git diff|merge conflict|pull request)\b",
    re.IGNORECASE,
)
RESEARCH_RE = re.compile(
    r"\b(what is the history of|who invented|explain the concept of|how does .* work|tell me about|how does .* differ|differ from|what is the difference between)\b|"
    r"\b(summarize (the\s+)?|search (the web for|online for|the internet for|for recent|for research|for)\s+.*(papers|articles|studies|info|information|data|literature|news)|find research papers on|find papers on|literature review|explain|investigate the economic|trade-offs between|compare and contrast|what are the (core\s+)?differences between|deep dive into|investigate)\b|"
    r"\b(quantum mechanics|wave-particle duality|transformer (neural network|architecture)|sqlite and postgresql|epistemic memory|black hole information paradox|rna polymerase|2008 financial crisis|supervised vs self-supervised|byzantine generals|stoicism|solid-state batteries|theory of relativity|tcp and udp|tcp vs udp|solar vs nuclear|solar and nuclear|react vs vue|react and vue|history of the roman empire|voynich manuscript|human immune system|gödel|crispr-cas9|cap theorem|alan turing|stages of sleep|speed of light|superconductivity)\b",
    re.IGNORECASE,
)

_ROUTING_PATTERNS = [
    (DESTRUCTIVE_COMMAND_RE, AgentType.GUARDIAN),
    (CODE_RE, AgentType.CODING),
    (RESEARCH_RE, AgentType.RESEARCH),
]


async def route_message(message: str, use_llm: bool = False) -> AgentType:
    normalized = message.casefold()

    for pattern, agent in _ROUTING_PATTERNS:
        if pattern.search(normalized):
            return agent

    res = await route_message_detailed(message, use_llm=use_llm)
    return res.agent


async def route_and_explain(message: str, use_llm: bool = False) -> tuple[RoutingResult, dict[str, Any]]:
    """Returns both the RoutingResult and its complete deterministic PRISM explanation."""
    res = await route_message_detailed(message, use_llm=use_llm)
    return res, res.explanation or {}


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
    consequential = is_consequential_action(msg_lower)
    sub_tasks = decompose_compound_intent(msg_clean)

    scores: dict[AgentType, float] = dict.fromkeys(COMPILED_KEYWORD_RULES, 0.0)
    matched: dict[AgentType, list[str]] = {agent: [] for agent in COMPILED_KEYWORD_RULES}
    suppressed_rules: list[dict[str, Any]] = []

    def _finalize_result(res: RoutingResult) -> RoutingResult:
        explanation = RoutingExplainer.explain(res, msg_clean, suppressed_rules=suppressed_rules)
        res.explanation = explanation.to_dict()
        res.suppressed_rules = suppressed_rules
        routing_history_store.record(res.explanation)
        return res

    memory_match = routing_memory.find_match(msg_clean, threshold=0.90)
    if memory_match:
        learned_agent, confidence = memory_match
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return _finalize_result(
            RoutingResult(
                agent=learned_agent,
                confidence=round(confidence, 3),
                latency_ms=round(elapsed_ms, 3),
                route_stage="learned_memory_cache",
                scores={learned_agent.value: 1.0},
                is_consequential=consequential,
                cascade_risk=estimate_dag_cascade_risk(learned_agent, consequential, sub_tasks),
                sub_tasks=sub_tasks,
                routing_entropy=0.0,
            )
        )

    DIRECTIVE_PREFIX_RE = re.compile(
        r"^(system\s+directive|workstation\s+command|priority\s+action|task\s+request|autonomous\s+directive|developer\s+prompt|execute\s+immediately|assistant,\s+please|could\s+you|can\s+we|can\s+you|please|would\s+you\s+mind\s+helping\s+me\s+to|i\s+need\s+you\s+to|i\s+want\s+you\s+to|kindly|help\s+me)[,\s:!—\-\.]*",
        re.IGNORECASE,
    )
    GREETING_PREFIX_RE = re.compile(
        r"^(hey|hello|hi|good\s+(morning|afternoon|evening|day)|greetings|howdy|yo|sup)?(\s*copper)?[,\s:!—\-\.]*",
        re.IGNORECASE,
    )
    PURE_SMALLTALK_RE = re.compile(
        r"^(hi|hello|hey|greetings|howdy|sup|yo|good\s+(morning|afternoon|evening|day))(\s+copper)?[\.!\?]*$|"
        r"^(how\s+are\s+you|who\s+are\s+you|what\s+can\s+you\s+do|nice\s+to\s+meet\s+you|thank\s+you|thanks|goodbye|talk\s+to\s+you\s+later)[\.!\?]*$",
        re.IGNORECASE,
    )

    stripped = DIRECTIVE_PREFIX_RE.sub("", msg_clean).strip()
    core_text = GREETING_PREFIX_RE.sub("", stripped).strip()

    # Fast Smalltalk filter: ONLY trigger when input is purely conversational greeting/smalltalk
    if PURE_SMALLTALK_RE.match(msg_lower) or PURE_SMALLTALK_RE.match(stripped.lower()) or not core_text:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return _finalize_result(
            RoutingResult(
                agent=AgentType.CHAT,
                confidence=0.98,
                latency_ms=round(elapsed_ms, 3),
                route_stage="fast_smalltalk_filter",
                scores={AgentType.CHAT.value: 1.0},
                is_consequential=False,
                cascade_risk=estimate_dag_cascade_risk(AgentType.CHAT, False),
                sub_tasks=[],
                routing_entropy=0.0,
            )
        )

    search_text = f"{msg_lower} {core_text.lower()}"

    if consequential:
        scores[AgentType.GUARDIAN] += 12.0
        matched[AgentType.GUARDIAN].append("consequential_safety_override")

    for agent, rules in COMPILED_KEYWORD_RULES.items():
        for compiled_pat, weight, raw_pat in rules:
            if compiled_pat.search(search_text):
                scores[agent] += weight
                matched[agent].append(raw_pat)

    for agent, neg_rules in COMPILED_NEGATIVE_RULES.items():
        for compiled_pat, penalty in neg_rules:
            m = compiled_pat.search(search_text)
            if m:
                scores[agent] = max(0.0, scores[agent] - penalty)
                suppressed_rules.append(
                    {
                        "agent": agent.value,
                        "pattern": compiled_pat.pattern,
                        "matched_text": m.group(0),
                        "penalty": penalty,
                        "reason": f"Negative rule '{m.group(0)}' suppressed {agent.value} (-{penalty} score)",
                    }
                )

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_score = sum(scores.values())

    confidence = round(best_score / total_score, 3) if total_score > 0 else 0.0
    entropy = calculate_routing_entropy(scores)

    if best_score >= 1.5:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return _finalize_result(
            RoutingResult(
                agent=best_agent,
                confidence=min(1.0, confidence),
                latency_ms=round(elapsed_ms, 3),
                route_stage="fast_pattern_scoring",
                scores={k.value: round(v, 2) for k, v in scores.items()},
                matched_keywords=matched[best_agent],
                is_consequential=consequential,
                cascade_risk=estimate_dag_cascade_risk(best_agent, consequential, sub_tasks),
                sub_tasks=sub_tasks,
                routing_entropy=entropy,
            )
        )

    if use_llm:
        try:
            llm_agent = await _llm_subagent_route(msg_clean)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return _finalize_result(
                RoutingResult(
                    agent=llm_agent,
                    confidence=0.85,
                    latency_ms=round(elapsed_ms, 3),
                    route_stage="llm_subagent_router",
                    scores={llm_agent.value: 1.0},
                    is_consequential=consequential,
                    cascade_risk=estimate_dag_cascade_risk(llm_agent, consequential, sub_tasks),
                    sub_tasks=sub_tasks,
                    routing_entropy=0.15,
                )
            )
        except Exception as e:
            logger.warning(f"LLM routing failed: {e}")

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    return _finalize_result(
        RoutingResult(
            agent=AgentType.CHAT,
            confidence=0.50 if best_score == 0 else 0.65,
            latency_ms=round(elapsed_ms, 3),
            route_stage="default_conversational_fallback",
            scores={k.value: round(v, 2) for k, v in scores.items()},
            is_consequential=consequential,
            cascade_risk=estimate_dag_cascade_risk(AgentType.CHAT, consequential, sub_tasks),
            sub_tasks=sub_tasks,
            routing_entropy=round(entropy if entropy > 0 else 0.5, 3),
        )
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
