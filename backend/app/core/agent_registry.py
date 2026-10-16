from dataclasses import dataclass
from enum import Enum
from typing import Any
from app.core.constants import AgentType

class ModelPoolTier(str, Enum):
    MODEL_1_CORE = "MODEL_1_CORE"
    MODEL_2_CODE = "MODEL_2_CODE"
    MODEL_3_OS = "MODEL_3_OS"
    MODEL_4_VISION = "MODEL_4_VISION"
    MODEL_5_WEB = "MODEL_5_WEB"
    MODEL_6_AUDIO = "MODEL_6_AUDIO"
    EMBEDDING_POOL = "EMBEDDING_POOL"
    WAKEWORD_POOL = "WAKEWORD_POOL"

@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    codename: str
    tier: ModelPoolTier
    domain: str
    blurb: str
    default_model: str
    status: str  # "active" | "planned"

CORE_ACTIVE_AGENTS: list[AgentDefinition] = [
    AgentDefinition(
        id=AgentType.CHAT.value,
        name="Chat",
        codename="ATLAS",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="General Reasoning & Conversation",
        blurb="Conversational dialogue, intent synthesis, and context orchestration.",
        default_model="qwen2.5:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.CODING.value,
        name="Coding",
        codename="VULCAN",
        tier=ModelPoolTier.MODEL_2_CODE,
        domain="Software Architecture & Syntax",
        blurb="Full-stack code generation, refactoring, and sandboxed test execution.",
        default_model="qwen2.5-coder-abliterated:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.DOCUMENT.value,
        name="Document",
        codename="SCRIBE",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Document Synthesis & Text Extraction",
        blurb="Academic papers, multi-page PDFs, structured reports, and briefs.",
        default_model="phi4:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.AUTOMATION.value,
        name="Automation",
        codename="DAEMON",
        tier=ModelPoolTier.MODEL_3_OS,
        domain="Desktop RPA & System Utilities",
        blurb="Deterministic OS automation, window navigation, and background task queues.",
        default_model="mistral-nemo:12b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.REMINDER.value,
        name="Reminder",
        codename="CHRONOS",
        tier=ModelPoolTier.MODEL_3_OS,
        domain="Time, Habits & Calendar",
        blurb="Calendar synchronization, contextual nudges, and commitment tracking.",
        default_model="qwen2.5:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.RESEARCH.value,
        name="Research",
        codename="PROMETHEUS",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Epistemic Research & Science",
        blurb="Multi-turn deep research loops, hypothesis verification, and literature synthesis.",
        default_model="deepseek-r1:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.VISION.value,
        name="Vision",
        codename="ARGUS",
        tier=ModelPoolTier.MODEL_4_VISION,
        domain="Visual Perception & Screen OCR",
        blurb="Multi-modal visual analysis, desktop screenshot OCR, and bounding box UI parsing.",
        default_model="qwen2.5-vl:3b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.IMAGE.value,
        name="Image",
        codename="PICASSO",
        tier=ModelPoolTier.MODEL_4_VISION,
        domain="Neural Image Generation",
        blurb="Offline local 1-step diffusion image generation studio.",
        default_model="sd_turbo",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.WEB_SEARCH.value,
        name="Web Search",
        codename="HERMES",
        tier=ModelPoolTier.MODEL_5_WEB,
        domain="Private Metasearch & Retrieval",
        blurb="Local SearXNG-backed privacy-preserving internet metasearch and HTML fact condensation.",
        default_model="qwen2.5:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.CAMPAIGN_INTELLIGENCE.value,
        name="Campaign Intelligence",
        codename="DELTA",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Ad-Tech & Anomaly Detection",
        blurb="Ad campaign telemetry analysis, conversion response modeling, and budget optimization.",
        default_model="deepseek-r1:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.PLANNER.value,
        name="Planner",
        codename="NEXUS",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Strategic DAG Planning",
        blurb="Complex instruction decomposition, task graph construction, and multi-agent DAG coordination.",
        default_model="deepseek-r1:14b",
        status="active"
    ),
    AgentDefinition(
        id=AgentType.GUARDIAN.value,
        name="Guardian",
        codename="AEGIS",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Safety & Security Gatekeeper",
        blurb="Continuous friction scoring, action reversibility analysis, and safety boundary enforcement.",
        default_model="qwen2.5:1.5b",
        status="active"
    ),
]

ROADMAP_PLANNED_AGENTS: list[AgentDefinition] = [
    AgentDefinition(
        id="behavior",
        name="Behavior",
        codename="PSYCHE",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Behavioral & Habit Analysis",
        blurb="Circadian rhythms, fatigue modeling, and user behavioral preference optimization.",
        default_model="planned:qwen2.5:14b",
        status="planned"
    ),
    AgentDefinition(
        id="nutrition",
        name="Nutrition",
        codename="SOLIS",
        tier=ModelPoolTier.MODEL_3_OS,
        domain="Biometric & Nutrition Telemetry",
        blurb="Biometric intake tracking, meal scheduling, and cognitive health correlations.",
        default_model="planned:smollm2:1.7b",
        status="planned"
    ),
    AgentDefinition(
        id="evaluator",
        name="Evaluator",
        codename="JUSTICIA",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="LLM-as-a-Judge Evaluation",
        blurb="Autonomous hallucination verification, rubric scoring, and synthetic output judging.",
        default_model="planned:deepseek-r1:14b",
        status="planned"
    ),
    AgentDefinition(
        id="orchestrator",
        name="Orchestrator",
        codename="SYMPHONY",
        tier=ModelPoolTier.MODEL_1_CORE,
        domain="Autonomous Swarm Orchestrator",
        blurb="High-density dynamic subagent swarming and consensus aggregation.",
        default_model="planned:qwen2.5:14b",
        status="planned"
    ),
    AgentDefinition(
        id="voice",
        name="Voice",
        codename="ECHO",
        tier=ModelPoolTier.MODEL_6_AUDIO,
        domain="Full-Duplex Speech & Audio",
        blurb="Sub-300ms bidirectional voice conversation with barge-in detection.",
        default_model="planned:kokoro+whisper",
        status="planned"
    ),
]

ALL_AGENTS: list[AgentDefinition] = CORE_ACTIVE_AGENTS + ROADMAP_PLANNED_AGENTS

def get_active_agent_count() -> int:
    return len(CORE_ACTIVE_AGENTS)

def get_planned_agent_count() -> int:
    return len(ROADMAP_PLANNED_AGENTS)

def get_model_pool_count() -> int:
    return len(ModelPoolTier)
