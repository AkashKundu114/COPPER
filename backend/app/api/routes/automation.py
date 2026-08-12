from fastapi import APIRouter
router = APIRouter(prefix='/automation', tags=['automation'])

@router.get('/status')
async def automation_status():
    return {'status': 'active', 'enabled': True}