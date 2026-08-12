from enum import Enum
CHROMA_COLLECTION_CHAT = 'copper_chat_history'
MEMORY_SEARCH_LIMIT = 5

class AgentType(str, Enum):
    CHAT = 'chat'
    CODING = 'coding'
    AUTOMATION = 'automation'
    REMINDER = 'reminder'
    RESEARCH = 'research'
    VISION = 'vision'
    PLANNER = 'planner'
    GUARDIAN = 'guardian'
    BEHAVIOR = 'behavior'
    NUTRITION = 'nutrition'
    EVALUATOR = 'evaluator'
    ORCHESTRATOR = 'orchestrator'

class GuardianLevel(int, Enum):
    LEVEL_0_EXECUTE = 0
    LEVEL_1_SUGGEST = 1
    LEVEL_2_CHALLENGE = 2
    LEVEL_3_SAFETY_BOUNDARY = 3

class LLMProvider(str, Enum):
    OLLAMA = 'ollama'
    OPENAI = 'openai'
    CLAUDE = 'claude'
    DEEPSEEK = 'deepseek'