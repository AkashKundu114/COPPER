from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.memory.vector_store import VectorStore
from app.core.logger import logger
from app.database.models.episode import Episode, EpisodeOutcome

_episode_store = VectorStore("copper_episodes")


class EpisodeService:
    async def record_episode(
        self,
        db: Session,
        context: str,
        project: str | None = None,
        task: str | None = None,
        goal: str | None = None,
        problem: str | None = None,
        decision: str | None = None,
        outcome: EpisodeOutcome | None = None,
        confidence: float = 0.5,
        tags: list[str] | None = None,
        user_id: int | None = None,
    ) -> Episode:
        ep = Episode(
            user_id=user_id,
            context=context,
            project=project,
            task=task,
            goal=goal,
            problem=problem,
            decision=decision,
            outcome=outcome,
            confidence=confidence,
            tags=tags,
        )
        db.add(ep)
        db.commit()
        db.refresh(ep)
        summary = f"Context: {context}. Task: {task or 'N/A'}. Problem: {problem or 'N/A'}. Decision: {decision or 'N/A'}. Outcome: {outcome.value if outcome else 'N/A'}."

        try:
            await _episode_store.add(
                text=summary,
                metadata={
                    "episode_id": ep.id,
                    "context": context,
                    "project": project or "",
                    "outcome": outcome.value if outcome else "",
                },
            )
        except Exception as e:
            logger.error(f"Failed to add episode {ep.id} to vector store: {e}")

        logger.info(f"Recorded episode {ep.id}")
        return ep

    async def find_similar_episodes(self, query: str, limit: int = 5) -> list[dict]:
        try:
            results = await _episode_store.search(query, n_results=limit)
            return [
                {
                    "document": r["document"],
                    "metadata": r.get("metadata", {}),
                    "similarity": round(1 - r.get("distance", 1), 3),
                }
                for r in results
                if r.get("distance", 99) < 1.5
            ]
        except Exception as e:
            logger.error(f"Failed to search similar episodes in vector store: {e}")
            return []

    def get_recent_episodes(self, db: Session, limit: int = 20, context: str | None = None) -> list[Episode]:
        q = db.query(Episode)
        if context:
            q = q.filter(Episode.context == context)
        return q.order_by(desc(Episode.created_at)).limit(limit).all()

    def get_episode_by_id(self, db: Session, episode_id: int) -> Episode | None:
        return db.query(Episode).filter(Episode.id == episode_id).first()


episode_service = EpisodeService()
