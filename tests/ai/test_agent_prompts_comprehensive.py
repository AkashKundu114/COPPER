from app.ai.llm.prompt_manager import build_messages, get_system_prompt
from app.core.constants import AgentType


def test_prompt_chat_agent():
    prompt = get_system_prompt(AgentType.CHAT)
    assert "CHAT" in prompt
    assert "COPPER" in prompt


def test_prompt_coding_agent():
    prompt = get_system_prompt(AgentType.CODING)
    assert "CODING" in prompt


def test_prompt_automation_agent():
    prompt = get_system_prompt(AgentType.AUTOMATION)
    assert "AUTOMATION" in prompt


def test_prompt_reminder_agent():
    prompt = get_system_prompt(AgentType.REMINDER)
    assert "REMINDER" in prompt


def test_prompt_research_agent():
    prompt = get_system_prompt(AgentType.RESEARCH)
    assert "RESEARCH" in prompt


def test_prompt_vision_agent():
    prompt = get_system_prompt(AgentType.VISION)
    assert "VISION" in prompt


def test_prompt_planner_agent():
    prompt = get_system_prompt(AgentType.PLANNER)
    assert "PLANNER" in prompt


def test_prompt_guardian_agent():
    prompt = get_system_prompt(AgentType.GUARDIAN)
    assert "GUARDIAN" in prompt


def test_prompt_epistemic_context_injection():
    context = "User is building a high-frequency trading bot in Rust"
    prompt = get_system_prompt(AgentType.CODING, memory_context=context)
    assert context in prompt
    assert "Epistemic Context" in prompt


def test_messages_builder_empty_user():
    msgs = build_messages("System", [], "")
    assert len(msgs) == 2
    assert msgs[-1]["content"] == ""
