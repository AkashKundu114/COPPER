from fastapi import APIRouter, HTTPException
from typing import List

from app.ai.ambient.cognitive_load import cognitive_load_detector, CognitiveProfile

router = APIRouter(prefix="/cognitive", tags=["cognitive-load"])

@router.get("/state", response_model=CognitiveProfile)
async def get_state():
    try:
        if not cognitive_load_detector.history:
            return cognitive_load_detector.detect_state()
        return cognitive_load_detector.history[-1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[CognitiveProfile])
async def get_history(hours: int = 24):
    try:
        return cognitive_load_detector.get_history(hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/should-suppress")
async def get_should_suppress():
    try:
        return {"suppress": cognitive_load_detector.should_suppress_notifications()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
