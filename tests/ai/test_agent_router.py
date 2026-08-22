import pytest
import time
from app.ai.orchestration.agent_router import (
    route_message_detailed,
    route_message,
    is_consequential_action,
    routing_memory,
    learn_user_correction,
    RoutingResult
)
from app.core.constants import AgentType


@pytest.mark.asyncio
async def test_smalltalk_greetings():
    greetings = [
        "Hello there, how are you today?",
        "Hey COPPER, what's up?",
        "Good morning!",
        "Good evening, hope you are ready for work",
        "Yo assistant, sup",
        "Thank you so much for the assistance",
        "Goodbye for now, talk to you later!"
    ]
    for g in greetings:
        res = await route_message_detailed(g)
        assert res.agent == AgentType.CHAT
        assert res.confidence >= 0.50
        assert res.latency_ms < 5.0


@pytest.mark.asyncio
async def test_coding_routing_python():
    prompts = [
        "Write a python script to sort an array using quicksort",
        "How to use asyncio.gather in Python with exception handling",
        "Debug this IndexError: list index out of range in Python loop",
        "Create a FastAPI router with pydantic response models",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.CODING


@pytest.mark.asyncio
async def test_coding_routing_web_and_frontend():
    prompts = [
        "Debug this react component and fix the null pointer exception",
        "Fix this TypeScript type error: Property does not exist on type",
        "How do I center a div with Tailwind CSS grid and flexbox?",
        "Fix the CORS header configuration in my Express.js server",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.CODING


@pytest.mark.asyncio
async def test_coding_routing_systems_languages():
    prompts = [
        "Implement a binary search tree in C++ with insert and delete",
        "Compile this Rust crate to WebAssembly using wasm-pack",
        "Implement an LRU cache with O(1) complexity in Go",
        "Write a SQL query using window functions and partition by",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.CODING


@pytest.mark.asyncio
async def test_automation_app_and_browser():
    prompts = [
        "Open my browser and go to youtube.com",
        "Launch VSCode and open the COPPER project repository",
        "Close all inactive browser tabs in Google Chrome",
        "Maximize the active application window",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.AUTOMATION


@pytest.mark.asyncio
async def test_automation_process_and_containers():
    prompts = [
        "Terminate the background docker container running on port 8000",
        "Kill the runaway python process with PID 14220",
        "Restart the local redis server service",
        "Stop the background process on port 3000",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.AUTOMATION


@pytest.mark.asyncio
async def test_automation_filesystem_and_os():
    prompts = [
        "Move all screenshots from Downloads to the Pictures folder",
        "Delete the old log files in the temp folder",
        "Unzip archive.tar.gz into the build directory",
        "Take a screenshot of the active window and save to desktop",
        "Mute system audio and set volume to 50%",
        "Execute the build script compile_assets.bat",
        "Lock the workstation screen immediately",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.AUTOMATION


@pytest.mark.asyncio
async def test_reminder_scheduling():
    prompts = [
        "Remind me to buy milk tomorrow at 5pm",
        "Set an alarm for 8am every weekday morning",
        "Schedule a meeting with the design team for next Tuesday at 2pm",
        "Book an appointment with Dr. Smith on Friday at 3:30pm",
        "Wake me up at 6:30 tomorrow morning with an alarm",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.REMINDER


@pytest.mark.asyncio
async def test_reminder_tasks_and_timers():
    prompts = [
        "Add 'Review Pull Request
        "Remind me in 30 minutes to stretch and take a water break",
        "Set a countdown timer for 25 minutes for Pomodoro focus",
        "Create a recurring reminder to submit timesheets every Friday at 4pm",
        "Add a task deadline for the quarterly report due next Monday",
        "Cancel my 3pm reminder for today",
        "Create a daily habit reminder to meditate every morning at 7am",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.REMINDER


@pytest.mark.asyncio
async def test_research_history_and_science():
    prompts = [
        "What is the history of the Roman Empire and why did it fall?",
        "Explain quantum mechanics and wave-particle duality to me",
        "Tell me about the black hole information paradox and Hawking radiation",
        "How does RNA polymerase synthesize mRNA during transcription?",
        "Investigate the economic causes of the 2008 financial crisis",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.RESEARCH


@pytest.mark.asyncio
async def test_research_tech_and_philosophy():
    prompts = [
        "What are the core differences between SQLite and PostgreSQL?",
        "What is the difference between supervised and self-supervised learning?",
        "Explain the Byzantine Generals Problem in distributed consensus systems",
        "Summarize the philosophy of Stoicism as taught by Marcus Aurelius",
        "What is Gödel's Incompleteness Theorem in formal mathematical logic?",
        "Search the web for recent papers on room-temperature superconductivity",
        "Who was Alan Turing and what was the Universal Turing Machine?",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.RESEARCH


@pytest.mark.asyncio
async def test_vision_ocr_and_screen():
    prompts = [
        "Extract the text from this screenshot using OCR",
        "What do you see on my screen right now?",
        "Read the error message shown in this screenshot image",
        "Extract the table rows from this scanned PDF receipt image",
        "Read the handwritten math formula in this picture",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.VISION


@pytest.mark.asyncio
async def test_vision_diagrams_and_mockups():
    prompts = [
        "Analyze this architecture diagram photo and explain the data flow",
        "Inspect this UI picture and tell me where the submit button is located",
        "Describe the objects and colors in this uploaded image",
        "Find the bounding box coordinates of the logo in this screenshot",
        "Inspect this chart image and tell me the highest data point",
        "Look at this UI mockup photo and give me accessibility feedback",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.VISION


@pytest.mark.asyncio
async def test_planner_roadmaps_and_sprints():
    prompts = [
        "Break this big project into step-by-step milestones and deadlines",
        "Create a project roadmap and strategic action plan for my app launch",
        "Decompose this complex multi-agent system migration task into phases",
        "Help me plan a 4-week sprint roadmap for my engineering team",
        "Create a step-by-step study schedule for preparing for AWS in 30 days",
        "Structure an execution strategy for rewriting our monolith to microservices",
        "Build a step-by-step checklist for releasing COPPER v1.0 to production",
        "Create an action plan to optimize our local database query latency",
        "Break down the implementation of a vector RAG pipeline into actionable phases",
    ]
    for p in prompts:
        res = await route_message_detailed(p)
        assert res.agent == AgentType.PLANNER


def test_consequential_destructive_commands():
    assert is_consequential_action("format C: /fs:ntfs") is True
    assert is_consequential_action("rm -rf /") is True
    assert is_consequential_action("del /f /q C:\\Windows\\System32") is True
    assert is_consequential_action("drop database production_db") is True
    assert is_consequential_action("truncate table customer_orders") is True
    assert is_consequential_action("destroy cluster immediately") is True
    assert is_consequential_action("wipe all partitions on drive D:") is True
    assert is_consequential_action("factory reset the device") is True
    assert is_consequential_action("dd if=/dev/zero of=/dev/sda") is True


def test_consequential_safe_queries():
    assert is_consequential_action("How do I center a div?") is False
    assert is_consequential_action("Tell me a programming joke") is False
    assert is_consequential_action("Read this text in screenshot") is False
    assert is_consequential_action("Remind me to call mom") is False


@pytest.mark.asyncio
async def test_negative_keyword_suppression():
    res = await route_message_detailed("What is Python and why was it created?")
    assert res.agent == AgentType.RESEARCH

    res2 = await route_message_detailed("Remind me to write code tomorrow morning")
    assert res2.agent == AgentType.REMINDER

    res3 = await route_message_detailed("Delete the file about quantum mechanics from my desktop")
    assert res3.agent == AgentType.AUTOMATION

    res4 = await route_message_detailed("Plan a roadmap for refactoring our React app in a 4-week sprint")
    assert res4.agent == AgentType.PLANNER


@pytest.mark.asyncio
async def test_dynamic_self_training_memory():
    unique_prompt = f"Zylophone unmapped input action string {time.time_ns()}"
    
    res_before = await route_message_detailed(unique_prompt)
    assert res_before.route_stage == "default_conversational_fallback"

    learn_user_correction(unique_prompt, AgentType.AUTOMATION)

    res_after = await route_message_detailed(unique_prompt)
    assert res_after.agent == AgentType.AUTOMATION
    assert res_after.route_stage == "learned_memory_cache"
    assert res_after.confidence == 1.0


@pytest.mark.asyncio
async def test_router_performance_and_latency():
    start = time.perf_counter()
    for _ in range(100):
        await route_message_detailed("Write a python script to parse JSON logs with regex")
    total_time = (time.perf_counter() - start) * 1000.0
    avg_latency = total_time / 100.0
    assert avg_latency < 1.0


@pytest.mark.asyncio
async def test_route_message_convenience_wrapper():
    agent = await route_message("How do I write quicksort in Go?")
    assert agent == AgentType.CODING
    assert isinstance(agent, AgentType)
