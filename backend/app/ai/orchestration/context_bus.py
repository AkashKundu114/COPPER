import json
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger
from app.database.redis_client import get_redis


@dataclass
class InterAgentMessage:
    id: str
    dag_id: str
    sender: str
    recipient: str
    message_type: str
    content: str
    timestamp: float = field(default_factory=time.time)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "dag_id": self.dag_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


class ContextBus:
    """Shared Context Bus for Multi-Agent Collaboration."""

    def __init__(self):
        self._contexts: dict[str, dict[str, Any]] = {}
        self._messages: dict[str, list[InterAgentMessage]] = {}
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], Coroutine[Any, Any, None]]]] = {}
        self._traces: dict[str, dict[str, Any]] = {}
        self._trace_order: list[str] = []

    async def set_context(self, dag_id: str, key: str, value: Any):
        """Store a key-value pair in the shared context for a DAG run."""
        if dag_id not in self._contexts:
            self._contexts[dag_id] = {}
        self._contexts[dag_id][key] = value

        try:
            r = await get_redis()
            if r:
                redis_key = f"copper:dag:{dag_id}:context"
                val_str = json.dumps(value) if not isinstance(value, str) else value
                await r.hset(redis_key, key, val_str)
                await r.expire(redis_key, 86400)
        except Exception as e:
            logger.debug(f"Redis set_context fallback to in-memory: {e}")

    async def get_context(self, dag_id: str, key: str, default: Any = None) -> Any:
        """Retrieve a value from the shared context."""
        if dag_id in self._contexts and key in self._contexts[dag_id]:
            return self._contexts[dag_id][key]

        try:
            r = await get_redis()
            if r:
                redis_key = f"copper:dag:{dag_id}:context"
                val = await r.hget(redis_key, key)
                if val is not None:
                    try:
                        return json.loads(val)
                    except Exception:
                        return val
        except Exception as e:
            logger.debug(f"Redis get_context error: {e}")

        return default

    async def get_all_context(self, dag_id: str) -> dict[str, Any]:
        """Retrieve all context key-values for a DAG run."""
        mem_ctx = self._contexts.get(dag_id, {}).copy()
        try:
            r = await get_redis()
            if r:
                redis_key = f"copper:dag:{dag_id}:context"
                raw = await r.hgetall(redis_key)
                if raw:
                    for k, v in raw.items():
                        try:
                            mem_ctx[k] = json.loads(v)
                        except Exception:
                            mem_ctx[k] = v
        except Exception as e:
            logger.debug(f"Redis get_all_context error: {e}")
        return mem_ctx

    async def send_message(
        self,
        dag_id: str,
        sender: str,
        recipient: str,
        message_type: str,
        content: str,
        payload: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> InterAgentMessage:
        """Pass a message from one specialist agent to another or to the bus."""
        msg_id = f"msg_{dag_id}_{int(time.time() * 1000)}_{len(self._messages.get(dag_id, [])) + 1}"
        msg = InterAgentMessage(
            id=msg_id,
            dag_id=dag_id,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            payload=payload or {},
        )

        if dag_id not in self._messages:
            self._messages[dag_id] = []
        self._messages[dag_id].append(msg)

        logger.info(f"ContextBus Inter-Agent [{sender} -> {recipient}] ({message_type}): {content[:80]}")

        try:
            r = await get_redis()
            if r:
                channel = f"copper:dag:{dag_id}:messages"
                await r.publish(channel, json.dumps(msg.to_dict()))
        except Exception as e:
            logger.debug(f"Redis pub/sub message publish error: {e}")

        if session_id:
            try:
                from app.api.websocket.manager import manager

                await manager.send_task_graph_update(
                    session_id,
                    "inter_agent_message",
                    msg.to_dict(),
                )
            except Exception as ws_err:
                logger.debug(f"ContextBus WebSocket message broadcast error: {ws_err}")

        await self._notify_subscribers(dag_id, {"type": "inter_agent_message", "data": msg.to_dict()})

        return msg

    def get_messages(self, dag_id: str) -> list[dict[str, Any]]:
        """Return chronological list of inter-agent messages for a DAG."""
        return [m.to_dict() for m in self._messages.get(dag_id, [])]

    async def publish_event(
        self,
        session_id: str | None,
        dag_id: str,
        event_type: str,
        payload: dict[str, Any],
    ):
        """Publish a DAG execution lifecycle event to Redis Pub/Sub,"""
        event_data = {
            "type": event_type,
            "dag_id": dag_id,
            "timestamp": time.time(),
            **payload,
        }

        try:
            r = await get_redis()
            if r:
                channel = f"copper:dag:{dag_id}:events"
                await r.publish(channel, json.dumps(event_data))
        except Exception as e:
            logger.debug(f"Redis pub/sub event publish error: {e}")

        if session_id:
            try:
                from app.api.websocket.manager import manager

                await manager.send_task_graph_update(session_id, event_type, payload)
            except Exception as ws_err:
                logger.debug(f"ContextBus WS event error: {ws_err}")

        await self._notify_subscribers(dag_id, event_data)

    def subscribe(self, dag_id: str, callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]):
        """Register an async callback listener for a DAG run."""
        if dag_id not in self._subscribers:
            self._subscribers[dag_id] = []
        self._subscribers[dag_id].append(callback)

    def unsubscribe(self, dag_id: str, callback: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]):
        """Unregister a listener."""
        if dag_id in self._subscribers and callback in self._subscribers[dag_id]:
            self._subscribers[dag_id].remove(callback)

    async def _notify_subscribers(self, dag_id: str, event: dict[str, Any]):
        subscribers = self._subscribers.get(dag_id, [])
        for sub in list(subscribers):
            try:
                await sub(event)
            except Exception as e:
                logger.warning(f"Subscriber callback error in ContextBus: {e}")

    def record_trace(self, dag_id: str, trace_data: dict[str, Any]):
        """Persist completed or in-progress DAG execution trace."""
        self._traces[dag_id] = trace_data
        if dag_id not in self._trace_order:
            self._trace_order.append(dag_id)
        if len(self._trace_order) > 200:
            oldest = self._trace_order.pop(0)
            self._traces.pop(oldest, None)
            self._contexts.pop(oldest, None)
            self._messages.pop(oldest, None)

    def get_trace(self, dag_id: str) -> dict[str, Any] | None:
        """Retrieve trace by DAG ID."""
        trace = self._traces.get(dag_id)
        if trace:
            trace["inter_agent_messages"] = self.get_messages(dag_id)
            trace["shared_context"] = self._contexts.get(dag_id, {})
        return trace

    def list_traces(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent DAG execution traces."""
        res = []
        for dag_id in reversed(self._trace_order[-limit:]):
            tr = self.get_trace(dag_id)
            if tr:
                res.append(tr)
        return res


context_bus = ContextBus()
