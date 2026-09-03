import asyncio
import base64
import ctypes
import io
import sys
from typing import Any

from PIL import Image, ImageGrab
import pyautogui

from app.ai.tools.registry import tool_registry
from app.core.logger import logger

# Configure PyAutoGUI fail-safe and timings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

# Ensure DPI awareness on Windows so screen coordinates match physical pixels
if sys.platform == "win32":
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        logger.debug(f"Could not set DPI awareness: {e}")


def ensure_interactive_desktop() -> None:
    """Ensure the calling thread is attached to the interactive Windows desktop."""
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x10000000)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception:
            pass


def get_screen_size() -> tuple[int, int]:
    """Return the primary screen resolution (width, height)."""
    try:
        w, h = pyautogui.size()
        return int(w), int(h)
    except Exception:
        return 1920, 1080


def get_active_window_title() -> str:
    """Retrieve the title of the current foreground/active window."""
    if sys.platform == "win32":
        try:
            import win32gui

            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                return title.strip()
        except Exception as e:
            logger.debug(f"Could not get active window title via win32gui: {e}")
    return ""


@tool_registry.tool(
    name="screenshot",
    description="Capture the full desktop screen as a base64 encoded PNG image.",
    parameters={
        "type": "object",
        "properties": {
            "max_dimension": {
                "type": "integer",
                "description": "Maximum width/height for downscaling (default 1920 to conserve LLM context).",
            }
        },
    },
    return_description="Dictionary containing base64 string, screen width, height, and scale factor.",
    guardian_level=0,
)
async def screenshot(max_dimension: int = 1920) -> dict[str, Any]:
    """Capture screen and return base64 encoded PNG string."""
    try:
        ensure_interactive_desktop()
        img = None

        # 1. Primary high-speed capture via mss (hardware-accelerated desktop capture)
        try:
            import mss

            with mss.MSS() as sct:
                # Primary monitor is sct.monitors[1]
                mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                sct_img = sct.grab(mon)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception as mss_err:
            logger.debug(f"mss capture fallback to ImageGrab: {mss_err}")

        # 2. Fallback capture via PIL ImageGrab
        if img is None:
            img = ImageGrab.grab(all_screens=False)

        orig_w, orig_h = img.size

        scale_factor = 1.0
        if max(orig_w, orig_h) > max_dimension and max_dimension > 0:
            scale_factor = max_dimension / float(max(orig_w, orig_h))
            new_w = max(1, int(orig_w * scale_factor))
            new_h = max(1, int(orig_h * scale_factor))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True)
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return {
            "status": "success",
            "image_b64": img_b64,
            "width": orig_w,
            "height": orig_h,
            "scaled_width": img.width,
            "scaled_height": img.height,
            "scale_factor": scale_factor,
        }
    except Exception as e:
        logger.error(f"screenshot capture error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="click",
    description="Click at specific (x, y) screen coordinates.",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "Horizontal pixel coordinate."},
            "y": {"type": "integer", "description": "Vertical pixel coordinate."},
            "button": {"type": "string", "description": "'left', 'right', or 'middle' (default 'left')."},
        },
        "required": ["x", "y"],
    },
    return_description="Result of mouse click execution.",
    guardian_level=1,
)
async def click(x: int, y: int, button: str = "left") -> dict[str, Any]:
    """Move to (x, y) and perform a mouse click."""
    try:
        btn = button.lower().strip() if button else "left"
        if btn not in ["left", "right", "middle"]:
            btn = "left"

        pyautogui.moveTo(x, y, duration=0.15)
        pyautogui.click(x=x, y=y, button=btn)
        await asyncio.sleep(0.3)  # Small delay for UI update

        return {
            "status": "success",
            "action": "click",
            "x": x,
            "y": y,
            "button": btn,
        }
    except Exception as e:
        logger.error(f"click error at ({x}, {y}): {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="double_click",
    description="Double-click at specific (x, y) screen coordinates.",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "Horizontal pixel coordinate."},
            "y": {"type": "integer", "description": "Vertical pixel coordinate."},
        },
        "required": ["x", "y"],
    },
    return_description="Result of mouse double click execution.",
    guardian_level=1,
)
async def double_click(x: int, y: int) -> dict[str, Any]:
    """Move to (x, y) and perform a double click."""
    try:
        pyautogui.moveTo(x, y, duration=0.15)
        pyautogui.doubleClick(x=x, y=y)
        await asyncio.sleep(0.3)

        return {
            "status": "success",
            "action": "double_click",
            "x": x,
            "y": y,
        }
    except Exception as e:
        logger.error(f"double_click error at ({x}, {y}): {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="type_text",
    description="Type text using keyboard simulation into the currently focused input field.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text string to type."},
            "interval": {"type": "number", "description": "Delay between keystrokes in seconds (default 0.02)."},
        },
        "required": ["text"],
    },
    return_description="Result of keyboard typing execution.",
    guardian_level=1,
)
async def type_text(text: str, interval: float = 0.02) -> dict[str, Any]:
    """Type text into active input field."""
    try:
        # Check if text contains non-ASCII characters that pyautogui.typewrite struggles with
        try:
            text.encode("ascii")
            pyautogui.typewrite(text, interval=max(0.01, float(interval)))
        except UnicodeEncodeError:
            import pyperclip

            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")

        await asyncio.sleep(0.3)
        return {"status": "success", "action": "type_text", "length": len(text)}
    except Exception as e:
        logger.error(f"type_text error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="hotkey",
    description="Execute a keyboard hotkey combination (e.g. ['ctrl', 's'] or ['enter']).",
    parameters={
        "type": "object",
        "properties": {
            "keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key names to press in combination.",
            }
        },
        "required": ["keys"],
    },
    return_description="Result of hotkey execution.",
    guardian_level=1,
)
async def hotkey(keys: list[str]) -> dict[str, Any]:
    """Press a key combination."""
    try:
        if not keys:
            return {"status": "error", "error": "No keys specified"}

        clean_keys = [str(k).lower().strip() for k in keys]
        pyautogui.hotkey(*clean_keys)
        await asyncio.sleep(0.3)

        return {"status": "success", "action": "hotkey", "keys": clean_keys}
    except Exception as e:
        logger.error(f"hotkey error with keys {keys}: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="scroll",
    description="Scroll the mouse wheel up or down at (x, y).",
    parameters={
        "type": "object",
        "properties": {
            "x": {"type": "integer", "description": "Horizontal pixel coordinate."},
            "y": {"type": "integer", "description": "Vertical pixel coordinate."},
            "direction": {"type": "string", "description": "'up' or 'down' (default 'down')."},
            "amount": {"type": "integer", "description": "Number of scroll clicks/steps (default 3)."},
        },
        "required": ["x", "y"],
    },
    return_description="Result of scroll execution.",
    guardian_level=1,
)
async def scroll(x: int, y: int, direction: str = "down", amount: int = 3) -> dict[str, Any]:
    """Scroll mouse wheel at (x, y)."""
    try:
        pyautogui.moveTo(x, y, duration=0.1)
        dir_clean = direction.lower().strip() if direction else "down"
        clicks = int(amount) if amount else 3

        # In pyautogui, positive is scroll up, negative is scroll down
        scroll_amount = clicks * 120 if dir_clean == "up" else -clicks * 120
        pyautogui.scroll(scroll_amount, x=x, y=y)
        await asyncio.sleep(0.3)

        return {
            "status": "success",
            "action": "scroll",
            "x": x,
            "y": y,
            "direction": dir_clean,
            "amount": clicks,
        }
    except Exception as e:
        logger.error(f"scroll error at ({x}, {y}): {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="wait",
    description="Pause execution for a given number of seconds to allow UI or page to load.",
    parameters={
        "type": "object",
        "properties": {
            "seconds": {"type": "number", "description": "Number of seconds to wait (default 1.0)."}
        },
    },
    return_description="Wait confirmation.",
    guardian_level=0,
)
async def wait(seconds: float = 1.0) -> dict[str, Any]:
    """Wait for UI updates."""
    sec = max(0.1, min(10.0, float(seconds)))
    await asyncio.sleep(sec)
    return {"status": "success", "action": "wait", "seconds": sec}
