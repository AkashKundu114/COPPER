from fastapi import APIRouter
router = APIRouter(prefix='/voice', tags=['voice'])

@router.get('/status')
async def voice_status():
    return {'status': 'ready', 'stt': 'whisper-local', 'tts': 'piper-local'}