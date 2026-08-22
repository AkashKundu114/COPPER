import pytest
from app.ai.orchestration.agent_router import route_message_detailed, route_message, is_consequential_action
from app.core.constants import AgentType


@pytest.mark.asyncio
async def test_smalltalk_filter():
    res = await route_message_detailed("Hello there, how are you today?")
    assert res.agent == AgentType.CHAT
    assert res.route_stage == "fast_smalltalk_filter"
    assert res.confidence >= 0.90
    assert res.latency_ms < 5.0


@pytest.mark.asyncio
async def test_coding_routing():
    prompts = [
        "Write a python script to sort an array using quicksort",
        "Debug this react component and fix the null error",
        "Implement a binary search tree in C++",
        "Fix this TypeScript type error: Property does not exist",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.CODING
        assert res.confidence >= 0.50


@pytest.mark.asyncio
async def test_automation_routing():
    prompts = [
        "Open my browser and go to youtube",
        "Terminate the background docker container on port 8000",
        "Move all screenshots from Downloads to the Pictures folder",
        "Kill the runaway python process with PID 14220",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.AUTOMATION


@pytest.mark.asyncio
async def test_reminder_routing():
    prompts = [
        "Remind me to buy milk tomorrow at 5pm",
        "Set an alarm for 8am every weekday",
        "Schedule a meeting with the design team next Tuesday",
        "Add 'Review PR #42' to my todo list",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.REMINDER


@pytest.mark.asyncio
async def test_research_routing():
    prompts = [
        "What is the history of the Roman Empire and why did it fall?",
        "Explain quantum mechanics and wave-particle duality to me",
        "What are the core differences between SQLite and PostgreSQL?",
        "Tell me about the black hole information paradox",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.RESEARCH


@pytest.mark.asyncio
async def test_vision_routing():
    prompts = [
        "Extract the text from this screenshot using OCR",
        "What do you see on my screen right now?",
        "Analyze this architecture diagram photo",
        "Inspect this UI picture and find the button",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.VISION


@pytest.mark.asyncio
async def test_planner_routing():
    prompts = [
        "Break this big project into step-by-step milestones and deadlines",
        "Create a project roadmap and strategic action plan",
        "Decompose this complex multi-agent system migration task",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.PLANNER


def test_consequential_action_detection():
    assert is_consequential_action("format C: /fs:ntfs") is True
    assert is_consequential_action("rm -rf /") is True
    assert is_consequential_action("del /f /q C:\\Windows\\System32") is True
    assert is_consequential_action("drop database production_db") is True
    assert is_consequential_action("How do I center a div?") is False
    assert is_consequential_action("Tell me a programming joke") is False


@pytest.mark.asyncio
async def test_negative_keyword_suppression():
    # "What is Python" should be RESEARCH, not CODING
    res = await route_message_detailed("What is Python and why was it created?")
    assert res.agent == AgentType.RESEARCH

    # "Remind me to write code" should be REMINDER, not CODING
    res2 = await route_message_detailed("Remind me to write code tomorrow morning")
    assert res2.agent == AgentType.REMINDER
