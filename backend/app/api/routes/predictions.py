from fastapi import APIRouter, HTTPException
from typing import Any
from pydantic import BaseModel

from app.ai.ambient.predictive_engine import predictive_engine
from app.core.logger import logger

router = APIRouter(prefix="/predictions", tags=["predictions"])

class PredictionStatusUpdate(BaseModel):
    status: str

@router.get("/today")
async def get_today_predictions() -> Any:
    try:
        predictions = predictive_engine.get_predictions_for_today()
        return {"predictions": [p.__dict__ for p in predictions]}
    except Exception as e:
        logger.error(f"Failed to get today's predictions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/patterns")
async def get_all_patterns() -> Any:
    try:
        patterns = predictive_engine.get_all_patterns()
        return {"patterns": patterns}
    except Exception as e:
        logger.error(f"Failed to get patterns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/analyze")
async def analyze_patterns() -> Any:
    try:
        predictions = predictive_engine.analyze_patterns()
        return {"message": "Analysis complete", "new_predictions": [p.__dict__ for p in predictions]}
    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{prediction_id}")
async def update_prediction(prediction_id: str, update: PredictionStatusUpdate) -> Any:
    try:
        predictive_engine.mark_prediction(prediction_id, update.status)
        return {"message": f"Prediction {prediction_id} marked as {update.status}"}
    except Exception as e:
        logger.error(f"Failed to update prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
