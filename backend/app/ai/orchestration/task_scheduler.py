try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    APSCHEDULER_AVAILABLE = True
except ImportError:
    AsyncIOScheduler = None
    IntervalTrigger = None
    APSCHEDULER_AVAILABLE = False

from app.core.anomaly_sentinel import sentinel
from app.core.logger import logger
from app.core.config import settings
import time

_scheduler = None

_last_reflection_time: float = 0.0
_last_reflection_alert_time: float = 0.0

async def _spider_sense_check():
    try:
        alerts = sentinel.run_checks()
        if alerts:
            from app.api.websocket.manager import manager

            for alert in alerts:
                await manager.broadcast_alert(alert)
    except Exception as e:
        logger.error(f"Spider-Sense check failed: {e}")

async def _reflection_cycle():
    global _last_reflection_time, _last_reflection_alert_time
    try:
        from app.services.self_model_service import self_model_service
        from app.ai.memory.persistent_memory import persistent_memory
        from app.ai.llm.ollama_client import ollama_client
        from app.ai.llm.model_manager import model_manager
        from app.core.config import settings
        from app.database.models.self_memory import SelfMemoryCategory

        # Apply decay on each cycle
        self_model_service.apply_decay()

        # Check for recent activity
        now = time.time()
        # Get recent conversation snippets
        recent_messages = []
        for sid, msgs in persistent_memory.sessions.items():
            for msg in msgs[-10:]:
                recent_messages.append(msg)
        
        if not recent_messages or len(recent_messages) < 3:
            _last_reflection_time = now
            return

        # Check if Ollama is available
        if not await ollama_client.is_available():
            return

        # One LLM call with the summarizer model
        summarizer_model = model_manager.get_model("subagents.summarizer", "llama3.1:8b")
        
        # Build recent activity summary
        activity = "\n".join([f"- [{m.get('role','?')}]: {m.get('content','')[:150]}" for m in recent_messages[-8:]])
        
        reflection_prompt = [
            {"role": "system", "content": (
                "You are COPPER's internal reflection process. Analyze recent activity and identify ONE of:\n"
                "1. A contradiction between things the user said\n"
                "2. An unresolved thread or open question\n"
                "3. A genuine new pattern or inference\n\n"
                "If nothing notable, respond with exactly: NOTHING_NOTABLE\n"
                "If something found, respond with a JSON object: {\"type\": \"open_question\" or \"position\", \"content\": \"...\", \"confidence\": 0.5-0.9}\n"
                "Be genuinely selective. Most of the time there IS nothing notable."
            )},
            {"role": "user", "content": f"Recent activity:\n{activity}"}
        ]

        response = await ollama_client.chat(reflection_prompt, model=summarizer_model)
        
        if "NOTHING_NOTABLE" in response:
            _last_reflection_time = now
            return

        # Try to parse structured output
        import json
        try:
            # Extract JSON from response
            json_match = response
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_match = response[start:end]
            data = json.loads(json_match)
            
            content = data.get("content", "")
            confidence = float(data.get("confidence", 0.5))
            cat_str = data.get("type", "position")
            category = SelfMemoryCategory.OPEN_QUESTION if cat_str == "open_question" else SelfMemoryCategory.POSITION

            if content:
                await self_model_service.record_reflection(content, category, confidence)

                # Only surface as toast if high confidence and rate-limited
                if confidence >= settings.REFLECTION_CONFIDENCE_THRESHOLD:
                    if (now - _last_reflection_alert_time) > 7200:  # 2-hour minimum gap
                        from app.api.websocket.manager import manager
                        await manager.push_proactive({
                            "alert_id": f"reflection_{int(now)}",
                            "severity": "info",
                            "category": "reflection",
                            "title": "COPPER noticed something",
                            "message": content,
                            "mode": "normal",
                            "suggested_actions": ["Tell me more", "Dismiss"],
                        })
                        _last_reflection_alert_time = now
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.debug(f"Reflection cycle produced non-structured output: {e}")

        _last_reflection_time = now
    except Exception as e:
        logger.error(f"Reflection cycle failed: {e}")


def start_scheduler():
    global _scheduler
    if not APSCHEDULER_AVAILABLE:
        logger.warning("APScheduler not installed, skipping background anomaly scheduler.")
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _spider_sense_check,
        IntervalTrigger(seconds=30),
        id="spider_sense",
        name="Spider-Sense Anomaly Sentinel",
        replace_existing=True,
    )
    _scheduler.add_job(
        _reflection_cycle,
        IntervalTrigger(seconds=settings.REFLECTION_INTERVAL_SECONDS if hasattr(settings, 'REFLECTION_INTERVAL_SECONDS') else 600),
        id="reflection_cycle",
        name="COPPER Reflection Cycle",
        replace_existing=True,
    )
    try:
        _scheduler.start()
        logger.info("Spider-Sense Anomaly Sentinel started (30s interval)")
        logger.info(f"COPPER Reflection Cycle started ({settings.REFLECTION_INTERVAL_SECONDS if hasattr(settings, 'REFLECTION_INTERVAL_SECONDS') else 600}s interval)")
    except Exception as e:
        logger.warning(f"Scheduler start deferred: {e}")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        if _scheduler.running:
            _scheduler.shutdown(wait=False)
        logger.info("Spider-Sense Anomaly Sentinel stopped")
        _scheduler = None
