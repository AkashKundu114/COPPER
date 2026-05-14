from enum import Enum


class AgentType(str, Enum):
    CHAT = "chat"
    CODING = "coding"
    AUTOMATION = "automation"
    REMINDER = "reminder"
    RESEARCH = "research"
    VISION = "vision"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


SYSTEM_PROMPT = """You are COPPER (Centralized Omnifunctional Personal Productivity and Execution Routine),
an advanced AI desktop assistant. You are intelligent, helpful, concise, and proactive.
You assist with coding, automation, research, reminders, and general tasks.
Respond naturally, keep answers focused and actionable."""

CHAT_HISTORY_LIMIT = 50
MEMORY_SEARCH_LIMIT = 5
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_CHAT = "copper_chat_memory"
CHROMA_COLLECTION_DOCS = "copper_documents"
