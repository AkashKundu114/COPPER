from app.ai.llm.prompt_manager import (
    BASE_COPPER_SYSTEM_PROMPT,
    ROUTING_PROMPT,
    build_messages,
    get_system_prompt,
)
from app.core.constants import AgentType


def test_base_copper_prompt_personality():
    assert "COPPER" in BASE_COPPER_SYSTEM_PROMPT
    assert "continuity" in BASE_COPPER_SYSTEM_PROMPT
    assert "Guardian" in BASE_COPPER_SYSTEM_PROMPT
    assert "WHO YOU ARE" in BASE_COPPER_SYSTEM_PROMPT
    assert "HOW YOU CHANGE" in BASE_COPPER_SYSTEM_PROMPT


def test_routing_prompt_contains_all_agents():
    for agent in [
        "chat",
        "coding",
        "automation",
        "reminder",
        "research",
        "vision",
        "planner",
        "guardian",
    ]:
        assert agent in ROUTING_PROMPT


def test_system_prompt_for_chat_agent():
    prompt = get_system_prompt(AgentType.CHAT)
    assert "Agent Role: CHAT" in prompt
    assert "User Epistemic Context" not in prompt


def test_system_prompt_for_coding_agent():
    prompt = get_system_prompt(
        AgentType.CODING, memory_context="Preferred language: Rust"
    )
    assert "Agent Role: CODING" in prompt
    assert "User Epistemic Context" in prompt
    assert "Preferred language: Rust" in prompt


def test_system_prompt_for_automation_agent():
    prompt = get_system_prompt(AgentType.AUTOMATION)
    assert "Agent Role: AUTOMATION" in prompt


def test_system_prompt_for_reminder_agent():
    prompt = get_system_prompt(AgentType.REMINDER)
    assert "Agent Role: REMINDER" in prompt


def test_system_prompt_for_research_agent():
    prompt = get_system_prompt(AgentType.RESEARCH)
    assert "Agent Role: RESEARCH" in prompt


def test_system_prompt_for_vision_agent():
    prompt = get_system_prompt(AgentType.VISION)
    assert "Agent Role: VISION" in prompt


def test_system_prompt_for_planner_agent():
    prompt = get_system_prompt(AgentType.PLANNER)
    assert "Agent Role: PLANNER" in prompt


def test_build_messages_structure():
    sys_prompt = "You are a test agent."
    history = [
        {"role": "user", "content": "Ping"},
        {"role": "assistant", "content": "Pong"},
    ]
    current = "Are you active?"
    messages = build_messages(sys_prompt, history, current)
    assert len(messages) == 4
    assert messages[0] == {"role": "system", "content": sys_prompt}
    assert messages[1] == {"role": "user", "content": "Ping"}
    assert messages[2] == {"role": "assistant", "content": "Pong"}
    assert messages[3] == {"role": "user", "content": current}


def test_build_messages_with_empty_history():
    messages = build_messages("System instruction", [], "User prompt only")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_build_messages_sliding_window():
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    messages = build_messages("System", long_history, "Latest")
    assert len(messages) == 8
    assert messages[-2]["content"] == "msg 19"
    assert messages[-1]["content"] == "Latest"
