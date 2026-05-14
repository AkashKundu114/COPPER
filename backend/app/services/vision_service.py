from typing import Optional
from app.ai.vision.ocr_engine import extract_text_from_image, preprocess_image_for_ocr
from app.ai.vision.screen_capture import capture_screen, get_active_window_title
from app.ai.vision.ui_detector import get_all_ui_elements, detect_error_dialogs
from app.ai.agents.vision_agent import vision_agent
from app.core.logger import logger


class VisionService:
    async def analyze_image(self, image_bytes: bytes, prompt: str = None) -> dict:
        prompt = prompt or "Describe this image in detail. Identify any text, UI elements, or important objects."
        try:
            description = await vision_agent.analyze_image(image_bytes, prompt)
            ocr_text = await self.extract_text(image_bytes)
            return {
                "description": description,
                "ocr_text": ocr_text,
                "has_text": bool(ocr_text.strip()),
            }
        except Exception as e:
            logger.error(f"Analyze image error: {e}")
            raise

    async def extract_text(self, image_bytes: bytes) -> str:
        try:
            processed = await preprocess_image_for_ocr(image_bytes)
            return await extract_text_from_image(processed)
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    async def capture_and_analyze(self, prompt: str = None) -> dict:
        screenshot = await capture_screen()
        window_title = await get_active_window_title()
        result = await self.analyze_image(screenshot, prompt)
        result["window_title"] = window_title
        result["screenshot_size"] = len(screenshot)
        return result

    async def detect_screen_errors(self) -> list[str]:
        screenshot = await capture_screen()
        return await detect_error_dialogs(screenshot)

    async def get_screen_elements(self) -> list[dict]:
        screenshot = await capture_screen()
        return await get_all_ui_elements(screenshot)

    async def screenshot(self) -> bytes:
        return await capture_screen()


vision_service = VisionService()
