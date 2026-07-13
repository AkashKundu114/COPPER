from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger
from app.api.routes import chat, agents, memory
from app.data.agents import AGENTS

app = FastAPI(title=settings.APP_NAME, description="COPPER orchestrator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(memory.router)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "status": "online", "agents": len(AGENTS)}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.on_event("startup")
async def on_startup():
    logger.info(f"{settings.APP_NAME} backend ready — {len(AGENTS)} agents loaded")
