import pytest
from app.core.constants import AgentType
from app.ai.llm.model_manager import model_manager, ModelManager
from app.ai.llm.prompt_manager import (
    ROUTING_PROMPT,
    BASE_COPPER_SYSTEM_PROMPT,
    get_system_prompt,
    build_messages
)


def test_model_manager_initialization():
    mgr = ModelManager()
    assert isinstance(mgr.manifest, dict)


def test_model_manager_dot_notation():
    model_name = model_manager.get_model("core_agents.chat", default="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")
    assert isinstance(model_name, str)
    assert len(model_name) > 0


def test_model_manager_invalid_path_fallback():
    fallback = "my-custom-fallback-model:8b"
    resolved = model_manager.get_model("nonexistent.agent.path.here", default=fallback)
    assert resolved == fallback


def test_routing_and_base_prompts():
    assert "router" in ROUTING_PROMPT.lower()
    assert "COPPER" in BASE_COPPER_SYSTEM_PROMPT


def test_get_system_prompt_all_agents():
    for agent in AgentType:
        prompt = get_system_prompt(agent, memory_context="User is coding a FastAPI project")
        assert agent.value.upper() in prompt
        assert "User is coding a FastAPI project" in prompt
        assert "COPPER" in prompt


def test_get_system_prompt_empty_context():
    prompt = get_system_prompt(AgentType.CHAT, memory_context="")
    assert "CHAT" in prompt
    assert "COPPER" in prompt


def test_build_messages():
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello! How can I help?"}
    ]
    msgs = build_messages(
        system_prompt="System prompt test",
        history=history,
        current_message="Can you help me?"
    )
    assert len(msgs) == 4
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "System prompt test"
    assert msgs[-1]["role"] == "user"
    assert msgs[-1]["content"] == "Can you help me?"


def test_build_messages_truncation():
    # Long history over 6 messages should be truncated to the last 6
    history = [{"role": "user", "content": f"msg {i}"} for i in range(12)]
    msgs = build_messages("System", history, "latest msg")
    assert len(msgs) == 1 + 6 + 1  # 1 system + 6 history + 1 current
