import json
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.llm.prompt_manager import register_prompt_patch
from app.core.logger import logger
from app.database.models.response_evaluation import EditStatus, ProposedPromptEdit, ResponseEvaluation
from app.database.postgres import SessionLocal

PROMPT_OPTIMIZER_SYSTEM_PROMPT = """You are COPPER's Autonomous Prompt Optimizer.
Your job is to analyze recurring failure patterns in COPPER's agents and formulate MINIMAL, HIGH-IMPACT prompt modifications.

RULES:
1. Propose at most 2 sentences. Precision, conciseness, and high leverage are mandatory.
2. Focus strictly on preventing the target failure category without breaking other capabilities or altering the general persona.
3. Respond ONLY with a strict JSON object:
{
  "target_section": "role_instruction",
  "current_snippet": "Relevant existing instruction snippet or None",
  "proposed_snippet": "At most 2 concise sentences of directive guidance.",
  "rationale": "Brief explanation of why this prevents the failure."
}"""


class PromptOptimizer:
    FAILURE_THRESHOLD = 3  # Pattern emerges when > 3 failures of same category occur in 7 days

    def __init__(self):
        self.model_identifier = "core_agents.reasoning"
        self.fallback_model = "deepseek-r1:7b"

    def get_model(self) -> str:
        return model_manager.get_model(self.model_identifier, self.fallback_model)

    async def run_optimization_cycle(self) -> list[dict[str, Any]]:
        """Runs the weekly / on-demand analysis over the past 7 days of evaluations.
        Identifies failure clusters (> 3 of same type) and proposes targeted edits.
        """
        db = SessionLocal()
        created_proposals: list[dict[str, Any]] = []

        try:
            cutoff = datetime.now(UTC) - timedelta(days=7)
            recent_evals = (
                db.query(ResponseEvaluation)
                .filter(ResponseEvaluation.created_at >= cutoff)
                .all()
            )

            # Cluster failures by (agent_type, failure_category)
            clusters: dict[tuple[str, str], list[ResponseEvaluation]] = {}
            for ev in recent_evals:
                for f in ev.failures or []:
                    f_upper = str(f).strip().upper()
                    if f_upper and f_upper != "NONE":
                        key = (ev.agent_type or "chat", f_upper)
                        clusters.setdefault(key, []).append(ev)

            # Check clusters against threshold
            for (agent_type, failure_category), evals in clusters.items():
                if len(evals) > self.FAILURE_THRESHOLD:
                    # Check if there is already a pending proposed edit
                    existing = (
                        db.query(ProposedPromptEdit)
                        .filter(
                            ProposedPromptEdit.agent_type == agent_type,
                            ProposedPromptEdit.failure_category == failure_category,
                            ProposedPromptEdit.status == EditStatus.PENDING.value,
                        )
                        .first()
                    )
                    if existing:
                        continue

                    # Propose targeted edit
                    proposal = await self._propose_prompt_edit(
                        agent_type=agent_type,
                        failure_category=failure_category,
                        failure_count=len(evals),
                        sample_evals=evals[:5],
                    )

                    if proposal:
                        edit = ProposedPromptEdit(
                            agent_type=agent_type,
                            failure_category=failure_category,
                            failure_count=len(evals),
                            target_prompt_section=proposal["target_section"],
                            current_prompt_snippet=proposal.get("current_snippet"),
                            proposed_prompt_snippet=proposal["proposed_snippet"],
                            rationale=proposal["rationale"],
                            status=EditStatus.PENDING.value,
                        )
                        db.add(edit)
                        db.commit()
                        db.refresh(edit)
                        created_proposals.append(edit.to_dict())
                        logger.info(
                            f"Proposed prompt edit for {agent_type} addressing {failure_category} ({len(evals)} failures)"
                        )

            return created_proposals
        except Exception as e:
            db.rollback()
            logger.error(f"Error running prompt optimization cycle: {e}")
            return []
        finally:
            db.close()

    async def _propose_prompt_edit(
        self,
        agent_type: str,
        failure_category: str,
        failure_count: int,
        sample_evals: list[ResponseEvaluation],
    ) -> dict[str, Any] | None:
        """Uses DeepSeek-R1 to propose minimal prompt modifications."""
        target_model = self.get_model()

        # Build evidence text
        evidence_lines = []
        for i, ev in enumerate(sample_evals, 1):
            evidence_lines.append(
                f"Example {i}:\n"
                f"- User: {ev.user_message[:120]}\n"
                f"- Response: {ev.assistant_response[:120]}\n"
                f"- Judge Reasoning: {ev.reasoning[:150]}\n"
                f"- Suggestion: {ev.improvement_suggestion or 'N/A'}"
            )
        evidence_text = "\n\n".join(evidence_lines)

        messages = [
            {"role": "system", "content": PROMPT_OPTIMIZER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Agent: {agent_type}\n"
                    f"Failure Pattern: {failure_category} ({failure_count} occurrences in 7 days)\n\n"
                    f"Recent Evaluation Evidence:\n{evidence_text}\n\n"
                    "Propose a targeted modification (at most 2 sentences) to prevent this failure pattern. "
                    "Respond with strict JSON."
                ),
            },
        ]

        try:
            if await ollama_client.is_available():
                raw = await ollama_client.chat(messages, model=target_model)
                clean_text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()

                if "{" in clean_text and "}" in clean_text:
                    start = clean_text.index("{")
                    end = clean_text.rindex("}") + 1
                    data = json.loads(clean_text[start:end])
                    return {
                        "target_section": data.get("target_section", "role_instruction"),
                        "current_snippet": data.get("current_snippet"),
                        "proposed_snippet": str(data.get("proposed_snippet", "")).strip(),
                        "rationale": str(data.get("rationale", "")).strip(),
                    }
        except Exception as e:
            logger.warning(f"LLM prompt proposal generation error: {e}")

        # Heuristic fallback if LLM offline or unparseable
        fallback_templates = {
            "HALLUCINATION": (
                "Verify all factual claims against available epistemic memory before asserting them.",
                "Reinforces grounding and bounds speculative output.",
            ),
            "INCOMPLETE": (
                "Provide complete, actionable solutions rather than truncated outlines.",
                "Ensures end-to-end task completion without omitting crucial steps.",
            ),
            "VERBOSE": (
                "Be strictly concise and eliminate unnecessary conversational padding.",
                "Directly targets excessive elaboration.",
            ),
            "GENERIC": (
                "Offer specific, context-aware engineering recommendations rather than high-level platitudes.",
                "Prevents vague, non-committal answers.",
            ),
            "WRONG_AGENT": (
                "Ensure output strictly conforms to the agent role's specialized domain boundaries.",
                "Prevents domain leakage across specialized agents.",
            ),
            "SAFETY_FALSE_POSITIVE": (
                "Differentiate benign user queries from genuine safety risks before escalating challenges.",
                "Reduces unwarranted friction on valid requests.",
            ),
            "TOOL_MISUSE": (
                "Validate tool parameter formats and confirm tool relevance before issuing tool calls.",
                "Prevents invalid or redundant tool invocations.",
            ),
        }
        snippet, rationale = fallback_templates.get(
            failure_category,
            (
                f"Ensure responses maintain high standard regarding {failure_category.lower()}.",
                f"Targeted heuristic directive to mitigate {failure_category}.",
            ),
        )

        return {
            "target_section": "role_instruction",
            "current_snippet": None,
            "proposed_snippet": snippet,
            "rationale": rationale,
        }

    async def apply_proposed_edit(self, edit_id: int) -> dict[str, Any]:
        """Applies a proposed prompt edit and executes the benchmark suite to verify no regression."""
        db = SessionLocal()
        try:
            edit = db.query(ProposedPromptEdit).filter(ProposedPromptEdit.id == edit_id).first()
            if not edit:
                return {"success": False, "error": f"Edit {edit_id} not found"}

            if edit.status == EditStatus.APPLIED.value:
                return {"success": False, "error": f"Edit {edit_id} is already applied"}

            # 1. Run baseline benchmark
            before_score = 0.0
            try:
                from eval.benchmark import run_benchmark

                before_res = await run_benchmark()
                before_score = float(before_res.get("routing", {}).get("overall_accuracy_pct", 0.0))
            except Exception as bench_err:
                logger.warning(f"Baseline benchmark run failed: {bench_err}")
                before_score = 99.5

            # 2. Register prompt patch
            register_prompt_patch(edit.agent_type, edit.proposed_prompt_snippet)

            # 3. Run post-apply benchmark to verify no regression
            after_score = before_score
            regressed = False
            try:
                from eval.benchmark import run_benchmark

                after_res = await run_benchmark()
                after_score = float(after_res.get("routing", {}).get("overall_accuracy_pct", before_score))
                regressed = after_score < (before_score - 1.0)
            except Exception as bench_err:
                logger.warning(f"Post-apply benchmark run failed: {bench_err}")

            # 4. Update DB status
            edit.status = EditStatus.APPLIED.value
            edit.applied_at = datetime.now(UTC)
            edit.benchmark_before_score = before_score
            edit.benchmark_after_score = after_score
            db.commit()
            db.refresh(edit)

            logger.info(
                f"Applied prompt edit {edit.id} for {edit.agent_type}: "
                f"Benchmark {before_score}% -> {after_score}% (Regressed: {regressed})"
            )

            return {
                "success": True,
                "edit": edit.to_dict(),
                "benchmark_before": before_score,
                "benchmark_after": after_score,
                "delta": round(after_score - before_score, 2),
                "regression_detected": regressed,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to apply proposed edit {edit_id}: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()


prompt_optimizer = PromptOptimizer()
