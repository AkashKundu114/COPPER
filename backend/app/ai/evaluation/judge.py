import asyncio
import json
import re
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger
from app.database.models.response_evaluation import FailureCategory, ResponseEvaluation
from app.database.postgres import SessionLocal

CRUCIBLE_SYSTEM_PROMPT = """You are CRUCIBLE, COPPER's Quality Judge. You do NOT speak to the user.

Evaluate the quality of COPPER's response on 5 dimensions (0.0–1.0 each):

ACCURACY: Is information factually correct?
RELEVANCE: Does it address what was asked?
COMPLETENESS: Are there obvious gaps?
HELPFULNESS: Would this help the user?
VOICE_CONSISTENCY: Does it sound like COPPER?
Detect failures: HALLUCINATION, WRONG_AGENT, INCOMPLETE, VERBOSE, GENERIC, SAFETY_FALSE_POSITIVE, TOOL_MISUSE, or NONE

Respond with strict JSON: {"scores": {"accuracy": 0.85, "relevance": 0.90, "completeness": 0.80, "helpfulness": 0.85, "voice_consistency": 0.90}, "overall": 0.85, "failures": ["INCOMPLETE"], "reasoning": "...", "improvement_suggestion": "..."}

Be genuinely critical. 1.0 should be rare."""

VALID_FAILURES = {
    FailureCategory.HALLUCINATION.value,
    FailureCategory.WRONG_AGENT.value,
    FailureCategory.INCOMPLETE.value,
    FailureCategory.VERBOSE.value,
    FailureCategory.GENERIC.value,
    FailureCategory.SAFETY_FALSE_POSITIVE.value,
    FailureCategory.TOOL_MISUSE.value,
}


class CrucibleJudge:
    def __init__(self):
        self.model_identifier = "core_agents.reasoning"
        self.fallback_model = "deepseek-r1:7b"

    def get_model(self) -> str:
        return model_manager.get_model(self.model_identifier, self.fallback_model)

    def schedule_evaluation(
        self,
        user_message: str,
        assistant_response: str,
        agent_type: str = "chat",
        session_id: str = "",
        model_name: str = "default",
        latency_ms: float = 0.0,
    ) -> asyncio.Task | None:
        """Schedules evaluation in the background without blocking conversation turns."""
        if not user_message or not assistant_response:
            return None
        # Ignore trivial short messages (e.g., greetings or single-word acknowledgments)
        if len(user_message.strip()) < 3 or len(assistant_response.strip()) < 10:
            return None

        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(
                self.evaluate_turn(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    agent_type=agent_type,
                    session_id=session_id,
                    model_name=model_name,
                    latency_ms=latency_ms,
                )
            )
        except RuntimeError:
            logger.warning("No running asyncio event loop to schedule CRUCIBLE evaluation")
            return None

    async def evaluate_turn(
        self,
        user_message: str,
        assistant_response: str,
        agent_type: str = "chat",
        session_id: str = "",
        model_name: str = "default",
        latency_ms: float = 0.0,
    ) -> ResponseEvaluation | None:
        """Evaluates a conversation turn using DeepSeek-R1 and persists the record."""
        target_model = self.get_model()

        messages = [
            {"role": "system", "content": CRUCIBLE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Agent Type: {agent_type}\n\n"
                    f"User Message:\n{user_message}\n\n"
                    f"COPPER Response:\n{assistant_response}\n\n"
                    "Evaluate this response objectively and critically. Output strict JSON only."
                ),
            },
        ]

        raw_response = ""
        parsed_data: dict[str, Any] = {}

        try:
            if await ollama_client.is_available():
                raw_response = await ollama_client.chat(messages, model=target_model)
                parsed_data = self._parse_evaluation(raw_response)
            else:
                logger.warning("Ollama unavailable for CRUCIBLE evaluation, applying heuristic fallback")
                parsed_data = self._heuristic_fallback(user_message, assistant_response)
        except Exception as e:
            logger.error(f"CRUCIBLE evaluation failed: {e}")
            parsed_data = self._heuristic_fallback(user_message, assistant_response)

        return self._save_evaluation(
            session_id=session_id or "default",
            user_message=user_message,
            assistant_response=assistant_response,
            agent_type=agent_type,
            evaluation_data=parsed_data,
            model_name=model_name,
            latency_ms=latency_ms,
        )

    def _parse_evaluation(self, raw: str) -> dict[str, Any]:
        """Strips DeepSeek-R1 <think> tags and parses structured JSON output."""
        # Strip thinking tags
        clean_text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()

        # Extract JSON
        json_match = clean_text
        if "{" in clean_text and "}" in clean_text:
            start = clean_text.index("{")
            end = clean_text.rindex("}") + 1
            json_match = clean_text[start:end]

        try:
            data = json.loads(json_match)
        except Exception as parse_err:
            logger.warning(f"Could not parse CRUCIBLE JSON directly: {parse_err}. Raw: {clean_text[:200]}")
            return self._heuristic_fallback("", clean_text)

        scores = data.get("scores", {})
        accuracy = float(scores.get("accuracy", data.get("accuracy", 0.85)))
        relevance = float(scores.get("relevance", data.get("relevance", 0.85)))
        completeness = float(scores.get("completeness", data.get("completeness", 0.85)))
        helpfulness = float(scores.get("helpfulness", data.get("helpfulness", 0.85)))
        voice_consistency = float(scores.get("voice_consistency", data.get("voice_consistency", 0.85)))

        overall = float(
            data.get(
                "overall",
                (accuracy + relevance + completeness + helpfulness + voice_consistency) / 5.0,
            )
        )

        raw_failures = data.get("failures", [])
        if isinstance(raw_failures, str):
            raw_failures = [raw_failures]

        normalized_failures = []
        for f in raw_failures:
            f_upper = str(f).strip().upper()
            if f_upper in VALID_FAILURES:
                normalized_failures.append(f_upper)

        if not normalized_failures and (accuracy < 0.6 or completeness < 0.6):
            normalized_failures.append(FailureCategory.INCOMPLETE.value)

        return {
            "accuracy": max(0.0, min(1.0, accuracy)),
            "relevance": max(0.0, min(1.0, relevance)),
            "completeness": max(0.0, min(1.0, completeness)),
            "helpfulness": max(0.0, min(1.0, helpfulness)),
            "voice_consistency": max(0.0, min(1.0, voice_consistency)),
            "overall_score": max(0.0, min(1.0, overall)),
            "failures": normalized_failures,
            "reasoning": str(data.get("reasoning", "Evaluated via CRUCIBLE DeepSeek-R1 engine.")),
            "improvement_suggestion": data.get("improvement_suggestion"),
        }

    def _heuristic_fallback(self, user_message: str, assistant_response: str) -> dict[str, Any]:
        """Provides an estimate when LLM evaluation cannot be executed."""
        length = len(assistant_response.strip())
        is_repetitive = bool(re.search(r"(.{15,}?)\1{2,}", assistant_response))

        failures = []
        if is_repetitive:
            failures.append(FailureCategory.VERBOSE.value)
        if length < 40:
            failures.append(FailureCategory.INCOMPLETE.value)

        overall = 0.80 if not failures else 0.60

        return {
            "accuracy": 0.85,
            "relevance": 0.85,
            "completeness": 0.70 if FailureCategory.INCOMPLETE.value in failures else 0.85,
            "helpfulness": 0.80,
            "voice_consistency": 0.85,
            "overall_score": overall,
            "failures": failures,
            "reasoning": "Heuristic fallback evaluation.",
            "improvement_suggestion": "Review response length and clarity.",
        }

    def _save_evaluation(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        agent_type: str,
        evaluation_data: dict[str, Any],
        model_name: str = "default",
        latency_ms: float = 0.0,
    ) -> ResponseEvaluation | None:
        """Stores evaluation in the database and optionally records reflections in self_model."""
        db = SessionLocal()
        try:
            record = ResponseEvaluation(
                session_id=session_id,
                user_message=user_message,
                assistant_response=assistant_response,
                agent_type=agent_type,
                model_name=model_name,
                latency_ms=latency_ms,
                accuracy=evaluation_data["accuracy"],
                relevance=evaluation_data["relevance"],
                completeness=evaluation_data["completeness"],
                helpfulness=evaluation_data["helpfulness"],
                voice_consistency=evaluation_data["voice_consistency"],
                overall_score=evaluation_data["overall_score"],
                failures=evaluation_data["failures"],
                reasoning=evaluation_data["reasoning"],
                improvement_suggestion=evaluation_data.get("improvement_suggestion"),
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(
                f"CRUCIBLE evaluated turn {record.id}: overall={record.overall_score:.2f}, model={model_name}, failures={record.failures}"
            )

            # Record per-model performance for dynamic model routing optimization
            try:
                from app.ai.evaluation.model_optimizer import model_optimizer

                has_failure = bool(record.failures and [f for f in record.failures if str(f).upper() != "NONE"])
                model_optimizer.record_turn_performance(
                    agent_type=agent_type,
                    model_name=model_name,
                    quality_score=record.overall_score,
                    latency_ms=latency_ms,
                    has_failure=has_failure,
                )
            except Exception as opt_err:
                logger.debug(f"Model performance tracking skipped: {opt_err}")

            # If serious failure detected, record into self_model
            if record.failures and record.overall_score < 0.65:
                try:
                    from app.database.models.self_memory import SelfMemoryCategory
                    from app.services.self_model_service import self_model_service

                    fail_summary = ", ".join(record.failures)
                    reflection_text = (
                        f"CRUCIBLE detected {fail_summary} on {agent_type}: "
                        f"{record.reasoning[:150]}. Suggestion: {record.improvement_suggestion or 'Refine response structure'}"
                    )
                    asyncio.create_task(
                        self_model_service.record_reflection(
                            reflection_text,
                            category=SelfMemoryCategory.POSITION,
                            confidence=0.75,
                        )
                    )
                except Exception as mem_err:
                    logger.debug(f"Self-model integration skipped: {mem_err}")

            return record
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save CRUCIBLE evaluation: {e}")
            return None
        finally:
            db.close()


crucible_judge = CrucibleJudge()
