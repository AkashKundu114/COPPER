from enum import Enum

CHROMA_COLLECTION_CHAT = "copper_chat_history"
MEMORY_SEARCH_LIMIT = 5


class AgentType(str, Enum):
    """
    Core specialized agent types in C.O.P.P.E.R.
    Each agent type corresponds to a fully implemented, registered agent with:
    - A dedicated handler/class subclassing BaseAgent
    - Prompt and tool bindings
    - An assigned Ollama model
    - Full automated test coverage
    """

    CHAT = "chat"
    """ATLAS: Primary conversational interface, dialogue orchestrator, and general reasoning."""

    CODING = "coding"
    """VULCAN: Full-stack code generation, refactoring, reverse engineering, and sandbox execution."""

    DOCUMENT = "document"
    """SCRIBE: Multi-format document authoring (PDF, Word DOCX, Markdown, HTML, spreadsheets)."""

    AUTOMATION = "automation"
    """DAEMON: OS and desktop automation, command-line execution, and system tool coordination."""

    REMINDER = "reminder"
    """CHRONOS: Schedule management, calendar events, focus blocks, deadlines, and reminders."""

    RESEARCH = "research"
    """PROMETHEUS: Hybrid RAG retrieval (vector + BM25 RRF), re-ranking, and citation grounding."""

    VISION = "vision"
    """ARGUS: Screen perception, UI bounding box coordinate detection, and desktop RPA actions."""

    IMAGE = "image"
    """PICASSO: Offline generative visual asset studio via Stable Diffusion / procedural canvas."""

    WEB_SEARCH = "web_search"
    """RAPTOR: Privacy-preserving web search via SearXNG with PII redaction and citation synthesis."""

    CAMPAIGN_INTELLIGENCE = "campaign_intelligence"
    """DELTA: Ad-tech telemetry monitoring, multi-method anomaly detection, and budget optimization."""

    PLANNER = "planner"
    """NEXUS: Complex instruction decomposition, DAG task graph construction, and multi-agent coordination."""

    GUARDIAN = "guardian"
    """AEGIS: Constitutional safety gatekeeper, action reversibility analysis, and friction index scoring."""


class GuardianLevel(int, Enum):
    LEVEL_0_EXECUTE = 0
    LEVEL_1_SUGGEST = 1
    LEVEL_2_CHALLENGE = 2
    LEVEL_3_SAFETY_BOUNDARY = 3


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertMode(str, Enum):
    NORMAL = "normal"
    FOCUSED = "focused"
    GUARDIAN = "guardian"
    EMERGENCY = "emergency"
    REFLECTION = "reflection"
