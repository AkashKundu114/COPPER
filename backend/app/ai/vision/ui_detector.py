from typing import Optional
from app.ai.vision.ocr_engine import get_text_regions
from app.ai.vision.screen_capture import capture_screen
from app.core.logger import logger


async def find_element_on_screen(
    target_text: str,
    screenshot: Optional[bytes] = None,
) -> Optional[dict]:
    """Find a UI element by its text label."""
    if screenshot is None:
        screenshot = await capture_screen()

    regions = await get_text_regions(screenshot)
    target_lower = target_text.lower()

    for region in regions:
        if target_lower in region["text"].lower():
            # Return center coordinates
            center_x = region["x"] + region["width"] // 2
            center_y = region["y"] + region["height"] // 2
            return {
                "text": region["text"],
                "x": center_x,
                "y": center_y,
                "bounds": region,
            }
    return None


async def click_element(target_text: str) -> bool:
    """Find and click a UI element by its text."""
    try:
        import pyautogui
        element = await find_element_on_screen(target_text)
        if element:
            pyautogui.click(element["x"], element["y"])
            logger.info(f"Clicked element: '{target_text}' at ({element['x']}, {element['y']})")
            return True
        logger.warning(f"Element not found: '{target_text}'")
        return False
    except Exception as e:
        logger.error(f"Click element error: {e}")
        return False


async def get_all_ui_elements(screenshot: Optional[bytes] = None) -> list[dict]:
    """Get all text elements visible on screen."""
    if screenshot is None:
        screenshot = await capture_screen()
    return await get_text_regions(screenshot)


async def detect_error_dialogs(screenshot: Optional[bytes] = None) -> list[str]:
    """Detect error messages on screen."""
    elements = await get_all_ui_elements(screenshot)
    error_keywords = ["error", "failed", "exception", "warning", "cannot", "unable"]
    errors = []
    for el in elements:
        text_lower = el["text"].lower()
        if any(kw in text_lower for kw in error_keywords):
            errors.append(el["text"])
    return errors
