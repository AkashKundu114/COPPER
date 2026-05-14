import io
from typing import Optional
import numpy as np
from app.core.logger import logger


async def extract_text_from_image(image_bytes: bytes, lang: str = "eng") -> str:
    """Extract text from image bytes using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise


async def extract_text_from_file(file_path: str, lang: str = "eng") -> str:
    with open(file_path, "rb") as f:
        return await extract_text_from_image(f.read(), lang)


async def get_text_regions(image_bytes: bytes) -> list[dict]:
    """Get text bounding boxes from image."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        regions = []
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if text and int(data["conf"][i]) > 30:
                regions.append({
                    "text": text,
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "confidence": data["conf"][i],
                })
        return regions
    except Exception as e:
        logger.error(f"OCR regions error: {e}")
        return []


async def preprocess_image_for_ocr(image_bytes: bytes) -> bytes:
    """Enhance image for better OCR accuracy."""
    try:
        import cv2
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply threshold for better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Encode back to bytes
        success, buffer = cv2.imencode(".png", thresh)
        return bytes(buffer) if success else image_bytes
    except Exception as e:
        logger.warning(f"Image preprocessing error (using original): {e}")
        return image_bytes
