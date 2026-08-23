from sqlalchemy.orm import Session

from app.core.data_firewall import redact
from app.core.guardian import DisagreementLevel, GuardianVerdict, guardian_engine
from app.core.logger import logger
from app.database.models.audit_log import AuditLogEntry


class GuardianService:
    async def evaluate_action(
        self, proposed_action: str, context: dict, db: Session, session_id: str | None = None, actor: str = "system"
    ) -> GuardianVerdict:
        verdict = guardian_engine.evaluate(proposed_action, context)
        if verdict.level >= DisagreementLevel.CHALLENGE:
            db.add(
                AuditLogEntry(
                    session_id=session_id,
                    category="guardian_safety_block"
                    if verdict.level == DisagreementLevel.SAFETY
                    else "guardian_challenge",
                    actor=actor,
                    summary=redact(f"Guardian raised {verdict.level.name} on: {proposed_action[:200]}"),
                    detail=redact(verdict.reasoning or ""),
                )
            )
            db.commit()
            logger.info(f"Guardian verdict {verdict.level.name} for action: {proposed_action[:80]}")
        return verdict

    def log(
        self,
        db: Session,
        category: str,
        actor: str,
        summary: str,
        detail: str | None = None,
        session_id: str | None = None,
        scope: str = "local",
    ) -> None:
        db.add(
            AuditLogEntry(
                session_id=session_id,
                category=category,
                actor=actor,
                summary=redact(summary),
                detail=redact(detail) if detail else None,
                scope=scope,
            )
        )
        db.commit()


guardian_service = GuardianService()
