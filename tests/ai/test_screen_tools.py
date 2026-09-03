from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from PIL import Image

from app.ai.tools.builtin.screen_tools import (
    click,
    double_click,
    get_active_window_title,
    get_screen_size,
    hotkey,
    screenshot,
    scroll,
    type_text,
    wait,
)
from app.ai.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_screen_tools_registered():
    """Verify all screen tools are properly registered in ToolRegistry."""
    for tool_name in ["screenshot", "click", "double_click", "type_text", "hotkey", "scroll", "wait"]:
        tool = tool_registry.get(tool_name)
        assert tool is not None, f"Tool {tool_name} not registered in ToolRegistry"


def test_get_screen_size():
    """Verify get_screen_size returns valid dimensions."""
    w, h = get_screen_size()
    assert isinstance(w, int) and w > 0
    assert isinstance(h, int) and h > 0


@pytest.mark.asyncio
async def test_screenshot_capture():
    """Verify screenshot captures image and encodes to base64."""
    mock_img = Image.new("RGB", (800, 600), color="blue")
    with patch("mss.MSS", side_effect=Exception("mss disabled for test")), \
         patch("PIL.ImageGrab.grab", return_value=mock_img):
        res = await screenshot(max_dimension=1000)
        assert res["status"] == "success"
        assert len(res["image_b64"]) > 100
        assert res["width"] == 800
        assert res["height"] == 600
        assert res["scale_factor"] == 1.0


@pytest.mark.asyncio
async def test_screenshot_downscaling():
    """Verify screenshot scales down high-resolution images."""
    mock_img = Image.new("RGB", (3840, 2160), color="red")
    with patch("mss.MSS", side_effect=Exception("mss disabled for test")), \
         patch("PIL.ImageGrab.grab", return_value=mock_img):
        res = await screenshot(max_dimension=1920)
        assert res["status"] == "success"
        assert res["width"] == 3840
        assert res["height"] == 2160
        assert res["scaled_width"] == 1920
        assert res["scaled_height"] == 1080
        assert res["scale_factor"] == 0.5


@pytest.mark.asyncio
async def test_click_execution():
    """Verify click delegates to pyautogui with delay."""
    with patch("pyautogui.moveTo") as mock_move, patch("pyautogui.click") as mock_click, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await click(x=400, y=300, button="left")
        assert res["status"] == "success"
        assert res["action"] == "click"
        assert res["x"] == 400
        assert res["y"] == 300
        mock_move.assert_called_once_with(400, 300, duration=0.15)
        mock_click.assert_called_once_with(x=400, y=300, button="left")


@pytest.mark.asyncio
async def test_double_click_execution():
    """Verify double_click delegates to pyautogui."""
    with patch("pyautogui.moveTo") as mock_move, patch("pyautogui.doubleClick") as mock_dclick, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await double_click(x=250, y=180)
        assert res["status"] == "success"
        assert res["action"] == "double_click"
        mock_move.assert_called_once_with(250, 180, duration=0.15)
        mock_dclick.assert_called_once_with(x=250, y=180)


@pytest.mark.asyncio
async def test_type_text_execution():
    """Verify type_text types string via pyautogui."""
    with patch("pyautogui.typewrite") as mock_type, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await type_text(text="Hello world")
        assert res["status"] == "success"
        assert res["action"] == "type_text"
        assert res["length"] == 11
        mock_type.assert_called_once_with("Hello world", interval=0.02)


@pytest.mark.asyncio
async def test_hotkey_execution():
    """Verify hotkey presses key combinations."""
    with patch("pyautogui.hotkey") as mock_hotkey, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await hotkey(keys=["ctrl", "s"])
        assert res["status"] == "success"
        assert res["action"] == "hotkey"
        assert res["keys"] == ["ctrl", "s"]
        mock_hotkey.assert_called_once_with("ctrl", "s")


@pytest.mark.asyncio
async def test_scroll_execution():
    """Verify scroll moves and scrolls wheel."""
    with patch("pyautogui.moveTo") as mock_move, patch("pyautogui.scroll") as mock_scroll, patch("asyncio.sleep", new_callable=AsyncMock):
        res = await scroll(x=500, y=400, direction="down", amount=5)
        assert res["status"] == "success"
        assert res["action"] == "scroll"
        mock_move.assert_called_once_with(500, 400, duration=0.1)
        # down direction is negative scroll
        mock_scroll.assert_called_once_with(-600, x=500, y=400)


@pytest.mark.asyncio
async def test_wait_execution():
    """Verify wait pauses execution."""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        res = await wait(seconds=1.5)
        assert res["status"] == "success"
        assert res["seconds"] == 1.5
        mock_sleep.assert_called_once_with(1.5)
