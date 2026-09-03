from datetime import UTC, datetime
from typing import Any

from app.core.logger import logger
from app.database.models.response_evaluation import AgentModelPerformance
from app.database.postgres import SessionLocal

# In-memory routing cache for microsecond lookup during chat turn execution
_active_model_routes: dict[str, str] = {}


class ModelSelectionOptimizer:
    def __init__(self):
        self._load_active_routes()

    def _load_active_routes(self):
        """Loads optimal model routes from database into memory cache."""
        try:
            db = SessionLocal()
            try:
                active_routes = (
                    db.query(AgentModelPerformance)
                    .filter(AgentModelPerformance.is_active_route == True)  # noqa: E712
                    .all()
                )
                for r in active_routes:
                    _active_model_routes[r.agent_type.lower()] = r.model_name
                logger.info(f"Loaded {len(_active_model_routes)} dynamic model routes: {_active_model_routes}")
            finally:
                db.close()
        except Exception:
            pass

    def get_optimal_model(self, agent_type: str) -> str | None:
        """Fast in-memory lookup for dynamic model selection."""
        if not agent_type:
            return None
        return _active_model_routes.get(agent_type.lower().strip())

    def record_turn_performance(
        self,
        agent_type: str,
        model_name: str,
        quality_score: float,
        latency_ms: float = 0.0,
        has_failure: bool = False,
    ) -> dict[str, Any]:
        """Tracks per-task performance metrics per model and evaluates dynamic routing."""
        if not agent_type or not model_name or model_name in ["default", "unknown"]:
            return {}

        clean_agent = agent_type.lower().strip()
        clean_model = model_name.strip()

        db = SessionLocal()
        try:
            perf = (
                db.query(AgentModelPerformance)
                .filter(
                    AgentModelPerformance.agent_type == clean_agent,
                    AgentModelPerformance.model_name == clean_model,
                )
                .first()
            )

            if not perf:
                perf = AgentModelPerformance(
                    agent_type=clean_agent,
                    model_name=clean_model,
                    sample_count=1,
                    avg_quality_score=quality_score,
                    avg_latency_ms=latency_ms,
                    failure_count=1 if has_failure else 0,
                    is_active_route=False,
                )
                db.add(perf)
            else:
                n = perf.sample_count
                perf.sample_count = n + 1
                perf.avg_quality_score = ((perf.avg_quality_score * n) + quality_score) / (n + 1)
                perf.avg_latency_ms = ((perf.avg_latency_ms * n) + latency_ms) / (n + 1)
                if has_failure:
                    perf.failure_count += 1
                perf.last_evaluated_at = datetime.now(UTC)

            db.commit()

            # Dynamic routing evaluation
            # Find all candidate models for this agent type with sufficient samples
            candidates = (
                db.query(AgentModelPerformance)
                .filter(AgentModelPerformance.agent_type == clean_agent)
                .all()
            )

            # Route to highest quality score with >= 3 samples
            eligible = [c for c in candidates if c.sample_count >= 3]
            if eligible:
                best_model = max(
                    eligible,
                    key=lambda c: (
                        c.avg_quality_score - (0.05 * (c.failure_count / max(1, c.sample_count))),
                        -c.avg_latency_ms,
                    ),
                )
                # Update routes
                for c in candidates:
                    c.is_active_route = c.id == best_model.id
                db.commit()

                # Update in-memory cache
                _active_model_routes[clean_agent] = best_model.model_name
                logger.info(
                    f"Dynamic model route updated for {clean_agent} -> {best_model.model_name} "
                    f"(Score: {best_model.avg_quality_score:.2f}, Latency: {best_model.avg_latency_ms:.1f}ms)"
                )

            return perf.to_dict()
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording model performance: {e}")
            return {}
        finally:
            db.close()

    def get_all_model_rankings(self) -> list[dict[str, Any]]:
        """Returns all model performance metrics grouped by agent."""
        db = SessionLocal()
        try:
            records = (
                db.query(AgentModelPerformance)
                .order_by(
                    AgentModelPerformance.agent_type.asc(),
                    AgentModelPerformance.avg_quality_score.desc(),
                )
                .all()
            )
            return [r.to_dict() for r in records]
        finally:
            db.close()


model_optimizer = ModelSelectionOptimizer()
