from fastapi import APIRouter

from app.ai.ambient.daily_briefing import daily_briefing_service

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("/morning")
async def get_morning_briefing():
    latest = await daily_briefing_service.get_latest_briefing()
    if latest:
        return latest
    return await daily_briefing_service.generate_morning_briefing()


@router.get("/eod")
async def get_eod_summary():
    latest = await daily_briefing_service.get_latest_summary()
    if latest:
        return latest
    return await daily_briefing_service.generate_eod_summary()


@router.post("/generate/morning")
async def force_generate_morning_briefing():
    return await daily_briefing_service.generate_morning_briefing()


@router.post("/generate/eod")
async def force_generate_eod_summary():
    return await daily_briefing_service.generate_eod_summary()
