import hashlib
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import desc

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.llm.prompt_manager import get_system_prompt
from app.core.constants import AgentType
from app.core.logger import logger
from app.database.models.lora_adapter import CuratedTrainingExample
from app.database.models.response_evaluation import ResponseEvaluation
from app.database.models.self_memory import SelfMemory, SelfMemoryCategory
from app.database.postgres import SessionLocal

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "training"
CURATED_EXAMPLES_FILE = DATA_DIR / "curated_examples.jsonl"

CHRYSALIS_CURATOR_PROMPT = """You are CHRYSALIS, COPPER's Training Data Curator. You do NOT speak to the user.

Evaluate if this interaction is suitable for fine-tuning:
INCLUDE if: score >= 0.85, no failures, genuine COPPER voice, non-trivial task
EXCLUDE if: user corrected it, hallucination detected, trivial greeting, mostly tool output

Respond with strict JSON: {"decision": "include"|"exclude", "reason": "...", "training_example": {"system": "...", "user": "...", "assistant": "..."}, "quality_tags": ["concise", "accurate"], "difficulty": "easy"|"medium"|"hard"}"""

TRIVIAL_PATTERNS = [
    r"^(hi|hello|hey|good\s+morning|good\s+evening|sup|yo)[!.,\s]*$",
    r"^(thanks|thank\s+you|thx|ok|okay|cool|k|got\s+it|bye|goodbye|cya)[!.,\s]*$",
    r"^(yes|no|sure|nope|yep)[!.,\s]*$",
]


class ChrysalisDataCurator:
    def __init__(self, output_path: Path = CURATED_EXAMPLES_FILE):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_identifier = "core_agents.reasoning"
        self.fallback_model = "deepseek-r1:7b"

    def get_model(self) -> str:
        return model_manager.get_model(self.model_identifier, self.fallback_model)

    def is_trivial(self, user_msg: str, assistant_msg: str) -> bool:
        """Determines whether an interaction is trivial greeting or single-word acknowledgment."""
        u = user_msg.strip().lower()
        a = assistant_msg.strip().lower()
        if len(u) < 4 or len(a) < 15:
            return True
        for pat in TRIVIAL_PATTERNS:
            if re.match(pat, u, re.IGNORECASE):
                return True
        return False

    def clean_text(self, text: str) -> str:
        """Strips tool call XML tags and thinking tags from training text."""
        cleaned = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<tool_result>.*?</tool_result>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()

    def compute_content_hash(self, user_msg: str, assistant_msg: str) -> str:
        """Computes deterministic hash for deduplication."""
        norm_u = " ".join(user_msg.strip().lower().split())
        norm_a = " ".join(assistant_msg.strip().lower().split())
        raw = f"{norm_u}||{norm_a}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def curate_from_evaluations(self, min_score: float = 0.85, limit: int = 50) -> dict[str, Any]:
        """Monitors CRUCIBLE response evaluations and extracts high-quality training triples."""
        db = SessionLocal()
        curated_count = 0
        skipped_count = 0

        try:
            # Query candidate evaluations
            evals = (
                db.query(ResponseEvaluation)
                .filter(ResponseEvaluation.overall_score >= min_score)
                .order_by(desc(ResponseEvaluation.created_at))
                .limit(limit)
                .all()
            )

            # Query recent correction sessions to exclude corrected turns
            corrections = (
                db.query(SelfMemory)
                .filter(SelfMemory.category == SelfMemoryCategory.CORRECTION)
                .all()
            )
            corrected_snippets = [
                c.content.lower().strip()
                for c in corrections
                if c.content and len(c.content.strip()) >= 5
            ]

            for ev in evals:
                # Exclude turns with detected failure categories
                valid_fails = [f for f in ev.failures or [] if str(f).upper() != "NONE"]
                if valid_fails:
                    skipped_count += 1
                    continue

                user_text = self.clean_text(ev.user_message)
                asst_text = self.clean_text(ev.assistant_response)

                # Exclude trivial interactions
                if self.is_trivial(user_text, asst_text):
                    skipped_count += 1
                    continue

                # Exclude if user corrected this response
                if any(
                    len(snip) >= 5 and (snip in user_text.lower() or (len(user_text) >= 10 and user_text[:30].lower() in snip))
                    for snip in corrected_snippets
                ):
                    skipped_count += 1
                    continue

                # Deduplication check
                c_hash = self.compute_content_hash(user_text, asst_text)
                existing = db.query(CuratedTrainingExample).filter(CuratedTrainingExample.content_hash == c_hash).first()
                if existing:
                    skipped_count += 1
                    continue

                # Classify difficulty & quality tags via LLM or heuristic
                classification = await self._classify_example(ev.agent_type, user_text, asst_text)

                if classification["decision"] != "include":
                    skipped_count += 1
                    continue

                # Generate system prompt appropriate for agent
                try:
                    agent_enum = AgentType(ev.agent_type.lower())
                except Exception:
                    agent_enum = AgentType.CHAT
                sys_prompt = get_system_prompt(agent_enum)

                example = CuratedTrainingExample(
                    session_id=ev.session_id,
                    agent_type=ev.agent_type,
                    system_prompt=sys_prompt,
                    user_message=user_text,
                    assistant_response=asst_text,
                    quality_score=ev.overall_score,
                    difficulty=classification["difficulty"],
                    quality_tags=classification["quality_tags"],
                    content_hash=c_hash,
                )
                db.add(example)
                db.commit()
                db.refresh(example)

                # Append to JSONL dataset
                self._append_to_jsonl(example)
                curated_count += 1

            logger.info(f"CHRYSALIS curated {curated_count} training examples (skipped {skipped_count})")
            return {
                "curated_new": curated_count,
                "skipped": skipped_count,
                "total_curated": db.query(CuratedTrainingExample).count(),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error during CHRYSALIS data curation: {e}")
            return {"error": str(e), "curated_new": 0}
        finally:
            db.close()

    async def _classify_example(self, agent_type: str, user_msg: str, asst_msg: str) -> dict[str, Any]:
        """Evaluates interaction suitability with CHRYSALIS prompt or heuristic fallback."""
        target_model = self.get_model()
        messages = [
            {"role": "system", "content": CHRYSALIS_CURATOR_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Agent: {agent_type}\n\n"
                    f"User Prompt:\n{user_msg}\n\n"
                    f"Assistant Response:\n{asst_msg}\n\n"
                    "Evaluate suitability for fine-tuning. Return strict JSON only."
                ),
            },
        ]

        try:
            if await ollama_client.is_available():
                raw = await ollama_client.chat(messages, model=target_model)
                clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
                if "{" in clean and "}" in clean:
                    start = clean.index("{")
                    end = clean.rindex("}") + 1
                    data = json.loads(clean[start:end])
                    return {
                        "decision": data.get("decision", "include"),
                        "difficulty": data.get("difficulty", "medium"),
                        "quality_tags": data.get("quality_tags", ["high_quality"]),
                    }
        except Exception as e:
            logger.debug(f"LLM classification fallback: {e}")

        # Heuristic classification
        has_code = "```" in asst_msg
        has_structure = "\n- " in asst_msg or "\n1. " in asst_msg
        length = len(asst_msg)

        if length > 800 or (has_code and length > 400):
            diff = "hard"
        elif length > 250 or has_code or has_structure:
            diff = "medium"
        else:
            diff = "easy"

        tags = []
        if has_code:
            tags.append("code")
        if has_structure:
            tags.append("structured")
        tags.append("direct_answer")

        return {
            "decision": "include",
            "difficulty": diff,
            "quality_tags": tags,
        }

    def _append_to_jsonl(self, example: CuratedTrainingExample):
        """Appends formatted training record to JSONL storage file."""
        record = {
            "id": example.id,
            "agent_type": example.agent_type,
            "difficulty": example.difficulty,
            "quality_tags": example.quality_tags or [],
            "messages": [
                {"role": "system", "content": example.system_prompt},
                {"role": "user", "content": example.user_message},
                {"role": "assistant", "content": example.assistant_response},
            ],
        }
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_curation_stats(self) -> dict[str, Any]:
        """Calculates dataset volume, difficulty distribution, and agent breakdown."""
        db = SessionLocal()
        try:
            total = db.query(CuratedTrainingExample).count()
            if total == 0:
                return {
                    "total_examples": 0,
                    "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0},
                    "agent_distribution": {},
                    "average_quality_score": 0.0,
                    "dataset_file_bytes": self.output_path.stat().st_size if self.output_path.exists() else 0,
                    "recent_examples": [],
                }

            all_examples = db.query(CuratedTrainingExample).all()
            diff_dist = {"easy": 0, "medium": 0, "hard": 0}
            agent_dist: dict[str, int] = {}
            total_score = 0.0

            for ex in all_examples:
                d = ex.difficulty.lower() if ex.difficulty else "medium"
                diff_dist[d] = diff_dist.get(d, 0) + 1
                ag = ex.agent_type.lower() if ex.agent_type else "chat"
                agent_dist[ag] = agent_dist.get(ag, 0) + 1
                total_score += ex.quality_score

            recent = (
                db.query(CuratedTrainingExample)
                .order_by(desc(CuratedTrainingExample.created_at))
                .limit(5)
                .all()
            )

            file_size = self.output_path.stat().st_size if self.output_path.exists() else 0

            return {
                "total_examples": total,
                "difficulty_distribution": diff_dist,
                "agent_distribution": agent_dist,
                "average_quality_score": round(total_score / total, 2),
                "dataset_file_bytes": file_size,
                "recent_examples": [r.to_dict() for r in recent],
            }
        finally:
            db.close()


data_curator = ChrysalisDataCurator()
