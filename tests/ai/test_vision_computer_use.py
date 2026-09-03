from unittest.mock import AsyncMock, patch
import pytest

from app.ai.agents.vision_agent import VisionAgent, vision_agent
from app.core.guardian import DisagreementLevel, guardian_engine


def test_vision_agent_initialization():
    """Verify VisionAgent is configured properly."""
    assert vision_agent.name == "IRIS (Computer Use Agent)"
    assert vision_agent.max_steps == 15
    assert "screenshot" in vision_agent.tools
    assert "click" in vision_agent.tools
    assert "type_text" in vision_agent.tools


def test_parse_action_tags():
    """Verify parse_action extracts thought and JSON from <action> tags."""
    agent = VisionAgent()
    output = (
        "I see a search bar in the center of the browser.\n"
        "I will click on it to focus.\n"
        '<action>{"type": "click", "x": 540, "y": 320, "button": "left"}</action>'
    )
    thought, action = agent.parse_action(output)
    assert "I see a search bar" in thought
    assert action == {"type": "click", "x": 540, "y": 320, "button": "left"}


def test_parse_action_markdown_and_bare_json():
    """Verify fallback parsing for markdown blocks and bare JSON."""
    agent = VisionAgent()

    # Markdown block
    md_output = "Navigating down.\n```json\n{\"type\": \"scroll\", \"x\": 500, \"y\": 500, \"direction\": \"down\"}\n```"
    thought, action = agent.parse_action(md_output)
    assert action == {"type": "scroll", "x": 500, "y": 500, "direction": "down"}

    # Bare JSON
    bare_output = "Pausing for loading.\n{\"type\": \"wait\", \"seconds\": 2}"
    thought, action = agent.parse_action(bare_output)
    assert action == {"type": "wait", "seconds": 2}


def test_guardian_window_safety():
    """Verify Guardian blocks interaction with blacklisted applications."""
    # Banking
    v_bank = guardian_engine.check_window_safety("Chase Online Banking - Google Chrome")
    assert v_bank.level == DisagreementLevel.SAFETY
    assert "sensitive keyword" in v_bank.reasoning

    # Medical
    v_med = guardian_engine.check_window_safety("MyChart Health Portal - Patient View")
    assert v_med.level == DisagreementLevel.SAFETY

    # Password Vault
    v_pwd = guardian_engine.check_window_safety("1Password Vault - Desktop")
    assert v_pwd.level == DisagreementLevel.SAFETY

    # Allowed Window
    v_ok = guardian_engine.check_window_safety("Visual Studio Code - app.py")
    assert v_ok.level == DisagreementLevel.EXECUTE


def test_guardian_typing_safety():
    """Verify Guardian blocks automated typing of passwords and tokens."""
    v_bad1 = guardian_engine.check_typing_safety("mySecretPassword123")
    assert v_bad1.level == DisagreementLevel.SAFETY

    v_bad2 = guardian_engine.check_typing_safety("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
    assert v_bad2.level == DisagreementLevel.SAFETY

    v_good = guardian_engine.check_typing_safety("print('Hello World')")
    assert v_good.level == DisagreementLevel.EXECUTE


@pytest.mark.asyncio
async def test_vision_agent_closed_loop_execution():
    """Verify closed-loop cycle: Screenshot -> Plan -> Action -> Screenshot -> Done."""
    agent = VisionAgent(max_steps=5)

    mock_screenshot = {
        "status": "success",
        "image_b64": "fake_base64_data",
        "width": 1920,
        "height": 1080,
        "scale_factor": 1.0,
    }

    step1_response = (
        "I observe the start button at bottom left.\n"
        '<action>{"type": "click", "x": 30, "y": 1050, "button": "left"}</action>'
    )
    step2_response = (
        "The start menu is now open. The task is finished.\n"
        '<action>{"type": "done", "summary": "Successfully clicked Start button and opened menu."}</action>'
    )

    with patch("app.ai.tools.builtin.screen_tools.screenshot", new_callable=AsyncMock) as mock_shot, \
         patch("app.ai.tools.builtin.screen_tools.get_active_window_title", return_value="Desktop"), \
         patch("app.ai.tools.builtin.screen_tools.get_screen_size", return_value=(1920, 1080)), \
         patch("app.ai.tools.builtin.screen_tools.click", new_callable=AsyncMock) as mock_click, \
         patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat, \
         patch("app.api.websocket.manager.manager.send", new_callable=AsyncMock) as mock_ws_send, \
         patch("app.api.websocket.manager.manager.broadcast", new_callable=AsyncMock) as mock_ws_broadcast:

        mock_shot.return_value = mock_screenshot
        mock_click.return_value = {"status": "success", "action": "click", "x": 30, "y": 1050}
        mock_chat.side_effect = [step1_response, step2_response]

        result = await agent.run("Open the start menu", session_id="test_session_1")

        assert "Task Completed" in result
        assert "Successfully clicked Start button" in result
        assert mock_chat.call_count == 2
        mock_click.assert_called_once_with(30, 1050, button="left")
        assert mock_ws_send.call_count >= 2


@pytest.mark.asyncio
async def test_vision_agent_guardian_window_halt():
    """Verify vision agent halts immediately if an active blacklisted window is focused."""
    agent = VisionAgent(max_steps=5)

    mock_screenshot = {
        "status": "success",
        "image_b64": "fake_base64_data",
        "width": 1920,
        "height": 1080,
        "scale_factor": 1.0,
    }

    with patch("app.ai.tools.builtin.screen_tools.screenshot", new_callable=AsyncMock) as mock_shot, \
         patch("app.ai.tools.builtin.screen_tools.get_active_window_title", return_value="Fidelity Investments - Portfolio"), \
         patch("app.ai.tools.builtin.screen_tools.get_screen_size", return_value=(1920, 1080)), \
         patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat:

        mock_shot.return_value = mock_screenshot

        result = await agent.run("Click the transfer button", session_id="test_session_2")

        assert "Guardian Intervention" in result
        assert "Fidelity Investments - Portfolio" in result
        # Ensure LLM was not even called on sensitive screen
        assert mock_chat.call_count == 0


@pytest.mark.asyncio
async def test_vision_agent_fast_ui_grounding():
    """Verify 2-stage grounding: Qwen2-VL-2B locates target UI elements when coordinates are absent."""
    agent = VisionAgent(max_steps=3)

    mock_grounding_response = '{"found": true, "x": 640, "y": 480, "box": [450, 600, 510, 680], "label": "Search Box"}'

    with patch("app.ai.llm.ollama_client.ollama_client.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_grounding_response
        grounded = await agent.ground_ui_element("Search Box", "fake_b64", 1920, 1080)

        assert grounded is not None
        assert grounded["found"] is True
        assert grounded["x"] == 640
        assert grounded["y"] == 480
