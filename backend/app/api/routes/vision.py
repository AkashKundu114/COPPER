from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import Response
from typing import Optional
from app.services.vision_service import vision_service
from app.core.logger import logger

router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
):
    try:
        image_bytes = await image.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        result = await vision_service.analyze_image(image_bytes, prompt)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vision analyze error: {e}")
        raise HTTPException(status_code=500, detail="Image analysis failed")


@router.post("/ocr")
async def extract_text(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        text = await vision_service.extract_text(image_bytes)
        return {"text": text, "char_count": len(text)}
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail="OCR failed")


@router.get("/screen/capture")
async def capture_screen():
    try:
        screenshot = await vision_service.screenshot()
        return Response(content=screenshot, media_type="image/png")
    except Exception as e:
        logger.error(f"Screen capture error: {e}")
        raise HTTPException(status_code=500, detail="Screen capture failed")


@router.get("/screen/analyze")
async def analyze_screen(prompt: Optional[str] = None):
    try:
        return await vision_service.capture_and_analyze(prompt)
    except Exception as e:
        logger.error(f"Screen analyze error: {e}")
        raise HTTPException(status_code=500, detail="Screen analysis failed")


@router.get("/screen/errors")
async def detect_errors():
    try:
        errors = await vision_service.detect_screen_errors()
        return {"errors": errors, "count": len(errors)}
    except Exception as e:
        logger.error(f"Error detection error: {e}")
        raise HTTPException(status_code=500, detail="Error detection failed")


@router.get("/screen/elements")
async def get_screen_elements():
    try:
        elements = await vision_service.get_screen_elements()
        return {"elements": elements, "count": len(elements)}
    except Exception as e:
        logger.error(f"Screen elements error: {e}")
        raise HTTPException(status_code=500, detail="Element detection failed")
