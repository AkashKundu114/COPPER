import io
from typing import Optional, tuple
from app.core.logger import logger


async def capture_screen(region: Optional[tuple] = None) -> bytes:
    """Capture full screen or a region (x, y, width, height). Returns PNG bytes."""
    try:
        import pyautogui
        from PIL import Image
        screenshot = pyautogui.screenshot(region=region)
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Screen capture error: {e}")
        raise


async def capture_window(window_title: str) -> Optional[bytes]:
    """Capture a specific window by title."""
    try:
        import pyautogui
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            logger.warning(f"Window '{window_title}' not found")
            return None
        win = windows[0]
        region = (win.left, win.top, win.width, win.height)
        return await capture_screen(region)
    except Exception as e:
        logger.error(f"Window capture error: {e}")
        return None


async def get_screen_size() -> tuple[int, int]:
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        return (1920, 1080)


async def get_active_window_title() -> str:
    try:
        import pygetwindow as gw
        window = gw.getActiveWindow()
        return window.title if window else ""
    except Exception:
        return ""
