from fastapi import APIRouter

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/")
async def list_reminders():
    return {"reminders": []}
