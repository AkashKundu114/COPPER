import math
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.constants import AgentType

AGENT_DISPLAY_NAMES: dict[AgentType | str, str] = {
    AgentType.CODING: "AXIS (Coding Engineer)",
    AgentType.AUTOMATION: "FORGE (OS & Sandbox Automation)",
    AgentType.RESEARCH: "OMNI (Research & Analysis)",
    AgentType.DOCUMENT: "KINESIS (Document Architect)",
    AgentType.REMINDER: "CHRONOS (Temporal & Reminders)",
    AgentType.VISION: "IRIS (Vision & OCR)",
    AgentType.IMAGE: "PICASSO (Image Studio)",
    AgentType.PLANNER: "NEXUS (Strategic Planner)",
    AgentType.CHAT: "COPPER (Conversational Interface)",
    AgentType.GUARDIAN: "AEGIS (Safety Guardian)",
    "coding": "AXIS (Coding Engineer)",
    "automation": "FORGE (OS & Sandbox Automation)",
    "research": "OMNI (Research & Analysis)",
    "document": "KINESIS (Document Architect)",
    "reminder": "CHRONOS (Temporal & Reminders)",
    "vision": "IRIS (Vision & OCR)",
    "image": "PICASSO (Image Studio)",
    "planner": "NEXUS (Strategic Planner)",
    "chat": "COPPER (Conversational Interface)",
    "guardian": "AEGIS (Safety Guardian)",
}

AGENT_CODENAMES: dict[AgentType | str, str] = {
    AgentType.CODING: "AXIS",
    AgentType.AUTOMATION: "FORGE",
    AgentType.RESEARCH: "OMNI",
    AgentType.DOCUMENT: "KINESIS",
    AgentType.REMINDER: "CHRONOS",
    AgentType.VISION: "IRIS",
    AgentType.IMAGE: "PICASSO",
    AgentType.PLANNER: "NEXUS",
    AgentType.CHAT: "COPPER",
    AgentType.GUARDIAN: "AEGIS",
    "coding": "AXIS",
    "automation": "FORGE",
    "research": "OMNI",
    "document": "KINESIS",
    "reminder": "CHRONOS",
    "vision": "IRIS",
    "image": "PICASSO",
    "planner": "NEXUS",
    "chat": "COPPER",
    "guardian": "AEGIS",
}


@dataclass
class KeywordHighlight:
    term: str
    start: int
    end: int
    agent: str
    weight: float = 1.0


@dataclass
class ScoreItem:
    agent: str
    agent_name: str
    codename: str
    score: float
    percentage: float
    is_winner: bool = False


@dataclass
class SuppressedRule:
    agent: str
    agent_name: str
    codename: str
    pattern: str
    matched_text: str
    penalty: float
    reason: str


@dataclass
class StageProgressionItem:
    stage_id: str
    stage_number: int
    name: str
    status: str  # "matched", "passed", "bypassed", "evaluated"
    decision: str


@dataclass
class RoutingExplanation:
    id: str
    timestamp: float
    prompt: str
    agent: str
    agent_codename: str
    agent_display: str
    decision_summary: str
    confidence: float
    confidence_pct: int
    latency_ms: float
    route_stage: str
    scores: dict[str, float]
    score_breakdown: list[dict[str, Any]]
    matched_keywords: list[str]
    matched_terms: list[dict[str, Any]]
    suppressed_rules: list[dict[str, Any]]
    stage_progression: list[dict[str, Any]]
    is_consequential: bool
    cascade_risk: float
    sub_tasks: list[str]
    confidence_calibration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RoutingExplainer:
    """
    Purely deterministic explainer (PRISM: Predictive Routing with Interpretability & Systematic Metrics).
    Produces rich, human-readable explanations of agent routing decisions in < 0.05ms without LLM inference.
    """

    @classmethod
    def get_agent_codename(cls, agent: AgentType | str) -> str:
        key = agent.value if isinstance(agent, AgentType) else str(agent)
        return AGENT_CODENAMES.get(key, key.upper())

    @classmethod
    def get_agent_display(cls, agent: AgentType | str) -> str:
        key = agent.value if isinstance(agent, AgentType) else str(agent)
        return AGENT_DISPLAY_NAMES.get(key, key.capitalize())

    @classmethod
    def extract_keyword_matches(
        cls, prompt: str, matched_patterns: list[str], agent: AgentType | str
    ) -> list[KeywordHighlight]:
        """
        Extract exact character spans for matched words in the original prompt.
        """
        highlights: list[KeywordHighlight] = []
        if not prompt or not matched_patterns:
            return highlights

        lower_prompt = prompt.lower()
        agent_str = agent.value if isinstance(agent, AgentType) else str(agent)

        for pat in matched_patterns:
            try:
                for match in re.finditer(pat, lower_prompt, re.IGNORECASE):
                    start, end = match.span()
                    actual_term = prompt[start:end]
                    # Avoid duplicate overlapping spans
                    if not any(h.start == start and h.end == end for h in highlights):
                        highlights.append(
                            KeywordHighlight(
                                term=actual_term,
                                start=start,
                                end=end,
                                agent=agent_str,
                            )
                        )
            except Exception:
                continue

        # Sort by occurrence in prompt
        highlights.sort(key=lambda h: h.start)
        return highlights

    @classmethod
    def compute_score_breakdown(
        cls, scores: dict[str, float], winning_agent: AgentType | str
    ) -> list[ScoreItem]:
        """
        Formats normalized horizontal bar scores per agent.
        """
        winning_key = winning_agent.value if isinstance(winning_agent, AgentType) else str(winning_agent)
        total_score = sum(max(0.0, v) for v in scores.values())
        items: list[ScoreItem] = []

        for k, v in scores.items():
            pct = round((v / total_score) * 100.0, 1) if total_score > 0 else (100.0 if k == winning_key else 0.0)
            items.append(
                ScoreItem(
                    agent=k,
                    agent_name=cls.get_agent_display(k),
                    codename=cls.get_agent_codename(k),
                    score=round(v, 2),
                    percentage=pct,
                    is_winner=(k == winning_key),
                )
            )

        # Sort by score descending
        items.sort(key=lambda x: x.score, reverse=True)
        return items

    @classmethod
    def compute_confidence_calibration(
        cls,
        confidence: float,
        scores: dict[str, float],
        winning_agent: AgentType | str,
        routing_entropy: float,
        is_consequential: bool,
        cascade_risk: float,
    ) -> dict[str, Any]:
        """
        Determines calibrated confidence, margin over runner-up, and certainty tier.
        """
        sorted_scores = sorted(scores.values(), reverse=True)
        top_score = sorted_scores[0] if len(sorted_scores) > 0 else 1.0
        runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        margin = max(0.0, top_score - runner_up)

        # Platt / Sigmoid-like empirical calibration scaling
        entropy_penalty = min(0.15, routing_entropy * 0.08)
        calibrated_conf = max(0.50, min(0.99, confidence - entropy_penalty))
        if margin >= 3.0:
            calibrated_conf = min(0.99, calibrated_conf + 0.04)

        if calibrated_conf >= 0.88:
            tier = "HIGH_CERTAINTY"
            tier_desc = "Optimal single-agent determinism"
        elif calibrated_conf >= 0.70:
            tier = "MODERATE_CERTAINTY"
            tier_desc = "Strong candidate match with minor candidate competition"
        else:
            tier = "AMBIGUOUS"
            tier_desc = "Multi-specialist overlap or conversational intent"

        return {
            "raw_confidence": round(confidence, 3),
            "calibrated_confidence": round(calibrated_conf, 3),
            "calibrated_pct": int(round(calibrated_conf * 100)),
            "certainty_tier": tier,
            "certainty_description": tier_desc,
            "routing_entropy": round(routing_entropy, 3),
            "runner_up_margin": round(margin, 2),
            "is_consequential": is_consequential,
            "cascade_risk": round(cascade_risk, 3),
        }

    @classmethod
    def generate_stage_progression(
        cls,
        route_stage: str,
        winning_agent: AgentType | str,
        scores: dict[str, float],
        is_consequential: bool,
    ) -> list[StageProgressionItem]:
        """
        Reconstructs the execution progression across all 5 routing stages.
        """
        agent_codename = cls.get_agent_codename(winning_agent)
        agent_display = cls.get_agent_display(winning_agent)

        stages: list[StageProgressionItem] = []

        # Stage 0: Dynamic Learned Memory Cache
        s0_matched = route_stage == "learned_memory_cache"
        stages.append(
            StageProgressionItem(
                stage_id="learned_memory_cache",
                stage_number=0,
                name="Learned Memory Cache",
                status="matched" if s0_matched else "passed",
                decision=(
                    f"Hit verified user routing cache -> Dispatched directly to {agent_codename}"
                    if s0_matched
                    else "Cache miss -> Proceeded to Stage 1"
                ),
            )
        )

        # Stage 1: Fast Smalltalk / Greeting Filter
        s1_matched = route_stage == "fast_smalltalk_filter"
        stages.append(
            StageProgressionItem(
                stage_id="fast_smalltalk_filter",
                stage_number=1,
                name="Fast Smalltalk Filter",
                status="matched" if s1_matched else ("bypassed" if s0_matched else "passed"),
                decision=(
                    "Matched conversational greeting patterns -> Dispatched to COPPER"
                    if s1_matched
                    else ("Bypassed (handled in Stage 0)" if s0_matched else "No greeting detected -> Proceeded to Stage 2")
                ),
            )
        )

        # Stage 2: Weighted Pattern Scoring & Negative Suppression
        s2_matched = route_stage == "fast_pattern_scoring"
        top_score = max(scores.values()) if scores else 0.0
        stages.append(
            StageProgressionItem(
                stage_id="fast_pattern_scoring",
                stage_number=2,
                name="Weighted Pattern & Suppression",
                status="matched" if s2_matched else ("bypassed" if (s0_matched or s1_matched) else "passed"),
                decision=(
                    f"Specialist rules fired -> Selected {agent_display} with winning score {top_score:.1f}"
                    if s2_matched
                    else (
                        "Bypassed by prior stage"
                        if (s0_matched or s1_matched)
                        else f"Below threshold (score: {top_score:.1f} < 1.5) -> Proceeded to Stage 3/4"
                    )
                ),
            )
        )

        # Stage 3: Consequential Safety Boundary Flagging
        stages.append(
            StageProgressionItem(
                stage_id="consequential_safety",
                stage_number=3,
                name="Consequential Action Safety Gate",
                status="evaluated",
                decision=(
                    "⚠️ Consequential action pattern detected -> Flagged for Guardian Level 3 gate"
                    if is_consequential
                    else "Benign operation verified -> Execution cleared"
                ),
            )
        )

        # Stage 4: Micro-Router / Conversational Fallback
        s4_llm = route_stage == "llm_subagent_router"
        s4_fallback = route_stage == "default_conversational_fallback"
        stages.append(
            StageProgressionItem(
                stage_id="fallback_resolution",
                stage_number=4,
                name="Micro-Router / Fallback",
                status="matched" if (s4_llm or s4_fallback) else "bypassed",
                decision=(
                    f"Ambiguous query resolved via Ollama LLM Micro-Router -> {agent_codename}"
                    if s4_llm
                    else (
                        "Unmatched pattern fallback -> Routed to COPPER (Conversational Interface)"
                        if s4_fallback
                        else "Bypassed (Resolved deterministically in earlier stages)"
                    )
                ),
            )
        )

        return stages

    @classmethod
    def generate_decision_summary(
        cls,
        agent: AgentType | str,
        confidence: float,
        route_stage: str,
        matched_highlights: list[KeywordHighlight],
        prompt: str,
    ) -> str:
        """
        Generates the standard human-readable decision summary.
        Example: "Routed to AXIS (confidence: 97%) because 'write a script' matched CODING keywords"
        """
        codename = cls.get_agent_codename(agent)
        conf_pct = int(round(confidence * 100))
        agent_key = agent.value if isinstance(agent, AgentType) else str(agent)
        category_name = agent_key.upper()

        if route_stage == "fast_smalltalk_filter":
            return f"Routed to COPPER (confidence: {conf_pct}%) because message matched conversational greeting patterns"

        if route_stage == "learned_memory_cache":
            return f"Routed to {codename} (confidence: {conf_pct}%) via exact learned memory cache match"

        if route_stage == "llm_subagent_router":
            return f"Routed to {codename} (confidence: {conf_pct}%) via LLM micro-router evaluation"

        if route_stage == "default_conversational_fallback":
            return f"Routed to COPPER (confidence: {conf_pct}%) via general conversational fallback"

        # Pattern scoring stage
        if matched_highlights:
            trigger_word = matched_highlights[0].term.strip()
            if len(trigger_word) > 40:
                trigger_word = trigger_word[:37] + "..."
            return f"Routed to {codename} (confidence: {conf_pct}%) because '{trigger_word}' matched {category_name} keywords"

        return f"Routed to {codename} (confidence: {conf_pct}%) based on highest domain affinity score"

    @classmethod
    def explain(
        cls,
        result: Any,  # RoutingResult
        prompt: str,
        suppressed_rules: list[dict[str, Any]] | None = None,
    ) -> RoutingExplanation:
        """
        Takes a RoutingResult and the prompt, and generates a complete RoutingExplanation.
        """
        agent = getattr(result, "agent", getattr(result, "agent_type", AgentType.CHAT))
        confidence = float(getattr(result, "confidence", 0.5))
        latency_ms = float(getattr(result, "latency_ms", 0.0))
        route_stage = str(getattr(result, "route_stage", "fast_pattern_scoring"))
        scores = dict(getattr(result, "scores", {}))
        matched_keywords = list(getattr(result, "matched_keywords", []))
        is_consequential = bool(getattr(result, "is_consequential", False))
        cascade_risk = float(getattr(result, "cascade_risk", 0.0))
        sub_tasks = list(getattr(result, "sub_tasks", []))
        routing_entropy = float(getattr(result, "routing_entropy", 0.0))

        agent_key = agent.value if isinstance(agent, AgentType) else str(agent)
        codename = cls.get_agent_codename(agent)
        display_name = cls.get_agent_display(agent)

        # Extract keyword highlights from original prompt
        highlights = cls.extract_keyword_matches(prompt, matched_keywords, agent)

        # Format suppressed rules
        suppressed_list: list[dict[str, Any]] = []
        if suppressed_rules:
            for s in suppressed_rules:
                suppressed_agent = s.get("agent", "")
                suppressed_list.append(
                    {
                        "agent": suppressed_agent,
                        "agent_name": cls.get_agent_display(suppressed_agent),
                        "codename": cls.get_agent_codename(suppressed_agent),
                        "pattern": s.get("pattern", ""),
                        "matched_text": s.get("matched_text", ""),
                        "penalty": s.get("penalty", 0.0),
                        "reason": s.get("reason", f"Negative suppression penalty of -{s.get('penalty', 0)} applied"),
                    }
                )

        # Compute score breakdown
        score_breakdown = [asdict(item) for item in cls.compute_score_breakdown(scores, agent)]

        # Decision summary
        decision_summary = cls.generate_decision_summary(
            agent, confidence, route_stage, highlights, prompt
        )

        # Confidence calibration
        calibration = cls.compute_confidence_calibration(
            confidence, scores, agent, routing_entropy, is_consequential, cascade_risk
        )

        # Stage progression
        stage_progression = [
            asdict(s)
            for s in cls.generate_stage_progression(
                route_stage, agent, scores, is_consequential
            )
        ]

        explanation_id = f"prism-{int(time.time() * 1000)}-{abs(hash(prompt)) % 10000:04d}"

        return RoutingExplanation(
            id=explanation_id,
            timestamp=time.time(),
            prompt=prompt,
            agent=agent_key,
            agent_codename=codename,
            agent_display=display_name,
            decision_summary=decision_summary,
            confidence=confidence,
            confidence_pct=int(round(confidence * 100)),
            latency_ms=latency_ms,
            route_stage=route_stage,
            scores=scores,
            score_breakdown=score_breakdown,
            matched_keywords=matched_keywords,
            matched_terms=[asdict(h) for h in highlights],
            suppressed_rules=suppressed_list,
            stage_progression=stage_progression,
            is_consequential=is_consequential,
            cascade_risk=cascade_risk,
            sub_tasks=sub_tasks,
            confidence_calibration=calibration,
        )


class RoutingHistoryStore:
    """
    Thread-safe in-memory ring buffer storing recent routing decisions with full PRISM explanations.
    """

    def __init__(self, capacity: int = 200):
        self._capacity = capacity
        self._lock = threading.Lock()
        self._history: list[dict[str, Any]] = []

    def record(self, explanation: dict[str, Any] | RoutingExplanation):
        payload = explanation.to_dict() if isinstance(explanation, RoutingExplanation) else explanation
        with self._lock:
            self._history.insert(0, payload)
            if len(self._history) > self._capacity:
                self._history.pop()

    def get_history(self, limit: int = 50, agent_type: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._history)

        if agent_type:
            agent_clean = agent_type.strip().lower()
            items = [item for item in items if item.get("agent", "").lower() == agent_clean]

        return items[:limit]

    def clear(self):
        with self._lock:
            self._history.clear()


routing_history_store = RoutingHistoryStore()
