import json
import re
from typing import Any

from app.ai.branching.branch_manager import branch_manager
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger

DIFF_ANALYSIS_SYSTEM_PROMPT = """You are COPPER's Semantic Branch Analyzer.
Your task is to analyze two divergent conversation branches and provide an objective, structured comparison.
Respond ONLY with a valid JSON object matching this schema:
{
  "divergence_point": "Summary of where and why the conversation branched",
  "branch_a_summary": "Concise summary of trajectory and outcomes in Branch A",
  "branch_b_summary": "Concise summary of trajectory and outcomes in Branch B",
  "key_differences": [
    {"aspect": "Topic/Approach/Tooling", "branch_a": "Details in A", "branch_b": "Details in B"}
  ],
  "recommendation": "Objective assessment of which branch produced a better outcome and why",
  "mergeable_insights": ["Key actionable insight 1", "Key actionable insight 2"]
}"""


class DiffAnalyzer:
    """
    Analyzes semantic differences, outcomes, and mergeable insights
    between two conversation branches using DeepSeek-R1 / Ollama.
    """

    def __init__(self):
        self.model_identifier = "core_agents.reasoning"
        self.fallback_model = "deepseek-r1:14b"

    def get_model(self) -> str:
        try:
            return model_manager.get_model(self.model_identifier, self.fallback_model)
        except Exception:
            return self.fallback_model

    async def compare_branches(
        self,
        branch_a_id: str,
        branch_b_id: str,
    ) -> dict[str, Any]:
        """
        Performs natural language semantic diff between Branch A and Branch B.
        """
        branch_a = branch_manager.get_branch(branch_a_id)
        if not branch_a:
            raise ValueError(f"Branch '{branch_a_id}' not found.")

        branch_b = branch_manager.get_branch(branch_b_id)
        if not branch_b:
            raise ValueError(f"Branch '{branch_b_id}' not found.")

        msgs_a = branch_a.get("messages", [])
        msgs_b = branch_b.get("messages", [])

        # 1. Identify divergence point
        div_idx = 0
        min_len = min(len(msgs_a), len(msgs_b))
        for i in range(min_len):
            if msgs_a[i].get("content") == msgs_b[i].get("content"):
                div_idx = i
            else:
                break

        div_msg = msgs_a[div_idx] if div_idx < len(msgs_a) else (msgs_b[div_idx] if div_idx < len(msgs_b) else {})
        div_text = div_msg.get("content", "Common root of conversation")

        # 2. Extract divergent messages
        diff_a = msgs_a[div_idx + 1 :] or msgs_a[div_idx:]
        diff_b = msgs_b[div_idx + 1 :] or msgs_b[div_idx:]

        diff_a_formatted = "\n".join(
            [f"- [{m.get('role', 'user')}]: {m.get('content', '')[:250]}" for m in diff_a]
        ) or "No subsequent messages."

        diff_b_formatted = "\n".join(
            [f"- [{m.get('role', 'user')}]: {m.get('content', '')[:250]}" for m in diff_b]
        ) or "No subsequent messages."

        # 3. LLM comparison prompt
        user_prompt = (
            f"Compare two conversation branches that diverged from the same point.\n\n"
            f"DIVERGENCE POINT:\n{div_text}\n\n"
            f"BRANCH A ({branch_a.get('title', branch_a_id)}):\n{diff_a_formatted}\n\n"
            f"BRANCH B ({branch_b.get('title', branch_b_id)}):\n{diff_b_formatted}\n\n"
            f"Output strict JSON only."
        )

        messages = [
            {"role": "system", "content": DIFF_ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        target_model = self.get_model()

        try:
            if await ollama_client.is_available():
                raw = await ollama_client.chat(messages, model=target_model)
                parsed = self._parse_diff_json(raw)
                if parsed:
                    parsed["branch_a_id"] = branch_a_id
                    parsed["branch_b_id"] = branch_b_id
                    parsed["branch_a_title"] = branch_a.get("title", branch_a_id)
                    parsed["branch_b_title"] = branch_b.get("title", branch_b_id)
                    return parsed
        except Exception as e:
            logger.warning(f"LLM branch comparison failed, using structural fallback: {e}")

        # 4. Fallback structural comparison
        return self._heuristic_diff(
            branch_a=branch_a,
            branch_b=branch_b,
            div_text=div_text,
            diff_a=diff_a,
            diff_b=diff_b,
        )

    def _parse_diff_json(self, raw: str) -> dict[str, Any] | None:
        """Strips thinking tags and parses strict JSON output."""
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
        if "{" in clean and "}" in clean:
            s_idx = clean.index("{")
            e_idx = clean.rindex("}") + 1
            try:
                data = json.loads(clean[s_idx:e_idx])
                return {
                    "divergence_point": str(data.get("divergence_point", "Divergence occurred at shared point.")),
                    "branch_a_summary": str(data.get("branch_a_summary", "Explored trajectory A.")),
                    "branch_b_summary": str(data.get("branch_b_summary", "Explored trajectory B.")),
                    "key_differences": data.get("key_differences", []),
                    "recommendation": str(data.get("recommendation", "Both branches provide valid exploratory paths.")),
                    "mergeable_insights": data.get("mergeable_insights", []),
                }
            except Exception as e:
                logger.debug(f"JSON decode error in diff analyzer: {e}")
        return None

    def _heuristic_diff(
        self,
        branch_a: dict[str, Any],
        branch_b: dict[str, Any],
        div_text: str,
        diff_a: list[dict[str, str]],
        diff_b: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Provides a structured heuristic diff when LLM inference is offline."""
        title_a = branch_a.get("title", "Branch A")
        title_b = branch_b.get("title", "Branch B")

        len_a = len(diff_a)
        len_b = len(diff_b)

        summary_a = (
            f"Contains {len_a} turn(s). Primary response focus: '{diff_a[0].get('content', '')[:60]}...'"
            if diff_a
            else "No additional turns."
        )
        summary_b = (
            f"Contains {len_b} turn(s). Primary response focus: '{diff_b[0].get('content', '')[:60]}...'"
            if diff_b
            else "No additional turns."
        )

        differences = [
            {
                "aspect": "Trajectory Depth",
                "branch_a": f"{len_a} conversational turn(s) after divergence",
                "branch_b": f"{len_b} conversational turn(s) after divergence",
            },
            {
                "aspect": "Initial Response Focus",
                "branch_a": diff_a[0].get("content", "")[:90] if diff_a else "None",
                "branch_b": diff_b[0].get("content", "")[:90] if diff_b else "None",
            },
        ]

        # Recommendation based on completeness
        if len_a > len_b:
            rec = f"{title_a} developed deeper exploration with {len_a} interaction turns."
        elif len_b > len_a:
            rec = f"{title_b} developed deeper exploration with {len_b} interaction turns."
        else:
            rec = "Both branches offer balanced parallel explorations with equal turn depths."

        insights = []
        if diff_a:
            insights.append(f"Insight from {title_a}: {diff_a[-1].get('content', '')[:120]}")
        if diff_b:
            insights.append(f"Insight from {title_b}: {diff_b[-1].get('content', '')[:120]}")

        return {
            "branch_a_id": branch_a.get("branch_id"),
            "branch_b_id": branch_b.get("branch_id"),
            "branch_a_title": title_a,
            "branch_b_title": title_b,
            "divergence_point": div_text[:180],
            "branch_a_summary": summary_a,
            "branch_b_summary": summary_b,
            "key_differences": differences,
            "recommendation": rec,
            "mergeable_insights": insights,
        }


diff_analyzer = DiffAnalyzer()
