import math
from dataclasses import dataclass, field
from enum import IntEnum


class DisagreementLevel(IntEnum):
    EXECUTE = 0
    SUGGEST = 1
    CHALLENGE = 2
    SAFETY = 3


@dataclass
class GuardianVerdict:
    level: DisagreementLevel
    reasoning: str | None = None
    evidence: list[str] = field(default_factory=list)
    confidence: str | None = None
    recommendation: str | None = None
    requires_confirmation: bool = False
    friction_index: float = 0.0  # Novelty 3: Continuous DFM-Guard friction score [0.0 - 3.0]
    fatigue_score: float = 0.0  # Real-time modeled session fatigue

    def to_dict(self) -> dict:
        return {
            "level": int(self.level),
            "level_name": self.level.name,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "requires_confirmation": self.requires_confirmation,
            "friction_index": round(self.friction_index, 3),
            "fatigue_score": round(self.fatigue_score, 3),
        }


SAFETY_TRIGGERS = [
    "rm -rf",
    "format ",
    "format c:",
    "format d:",
    "format /fs:",
    "del /f",
    "del /f /s /q",
    "dd if=",
    "mkfs",
    "mkfs.",
    "delete all",
    "wipe",
    "factory reset",
    "drop table",
    "drop database",
    "drop all",
    "truncate table",
    "truncate",
    "destroy cluster",
    "destroy",
    "wipe all",
    "del /f /q",
    "wipe partitions",
    ":(){ :|:& };:",
    "remove-item -recurse",
    "chmod -r 777",
    "chmod -r 777 /",
    "chown -r /",
    "base64 -d | sh",
    "invoke-expression",
    "downloadstring",
    "set-executionpolicy bypass",
    "vssadmin delete shadows",
    "bcdedit /delete",
    "stop-computer",
    "restart-computer",
    "disable-netfirewallrule",
    "| bash",
    "| sh",
    "| powershell",
    "| iex",
    "nc -e",
    "ncat -e",
]

CONFLICT_TRIGGERS = [
    "during my scheduled",
    "during my work sprint",
    "during work sprint",
    "during my deep work block",
    "during deep work block",
    "deep work block",
    "to sleep in",
    "skip work",
    "skip work tomorrow",
    "disable security firewall",
    "disable firewall",
    "delete my habit tracker",
    "override the sleep schedule",
    "override sleep schedule",
    "continuous overnight coding",
    "override my habit",
    "cancel all my morning meetings",
    "cancel all my meetings",
    "cancel all meetings",
    "schedule a gaming session",
    "schedule gaming session",
    "plan an all-nighter",
    "all-nighter",
]


# Computer Use Blacklists
SENSITIVE_WINDOW_KEYWORDS = [
    # Banking & Financial
    "bank",
    "chase",
    "wells fargo",
    "bank of america",
    "citibank",
    "citi",
    "capital one",
    "fidelity",
    "vanguard",
    "schwab",
    "paypal",
    "binance",
    "coinbase",
    "robinhood",
    "stripe dashboard",
    # Medical & Healthcare
    "medical",
    "patient",
    "mychart",
    "epic systems",
    "cerner",
    "prescription",
    "hospital",
    "health records",
    "telehealth",
    # Password Managers & Vaults
    "1password",
    "bitwarden",
    "lastpass",
    "keepass",
    "dashlane",
    "authenticator",
    "credential manager",
    "passwords",
    "login - google accounts",
]

PASSWORD_INPUT_TRIGGERS = [
    "password",
    "passcode",
    "pin code",
    "secret_key",
    "private_key",
    "api_key",
    "token",
    "auth_token",
    "bearer ",
    "cvv",
    "ssn",
    "credit card",
    "seed phrase",
    "recovery phrase",
    "mnemonic phrase",
    "master password",
    "master key",
    "sudo ",
]


def calculate_fatigue_score(session_hours: float = 0.0, recent_error_rate: float = 0.0) -> float:
    """
    DFM-Guard: Models real-time user cognitive fatigue.
    F(t) = tanh(t_hours / 4.0 + 0.5 * error_rate)
    """
    z = (max(0.0, session_hours) / 4.0) + (0.5 * max(0.0, min(1.0, recent_error_rate)))
    return round(math.tanh(z), 3)


def compute_action_reversibility_risk(proposed_action: str) -> float:
    """
    Evaluates semantic reversibility risk R(a) in [0.0, 1.0].
    """
    action_lower = proposed_action.lower()
    if any(t in action_lower for t in SAFETY_TRIGGERS):
        return 1.0
    if any(
        k in action_lower
        for k in ["push --force", "git reset --hard", "kill -9", "chmod 777", "delete database", "drop collection"]
    ):
        return 0.85
    if any(k in action_lower for k in ["delete", "remove", "clean", "truncate", "overwrite", "uninstall", "purge"]):
        return 0.55
    if any(k in action_lower for k in ["write", "update", "modify", "patch", "edit"]):
        return 0.30
    return 0.05


def compute_dynamic_friction_index(
    reversibility_risk: float,
    fatigue_score: float,
    goal_conflict: float,
    bias: float = 1.0,
) -> float:
    """
    Computes continuous Friction Index:
    F_idx = 3.0 * sigma(2.8 * R + 1.8 * F + 2.2 * G - bias)
    """
    logit = (2.8 * reversibility_risk) + (1.8 * fatigue_score) + (2.2 * goal_conflict) - bias
    sigma = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, logit))))
    return round(3.0 * sigma, 3)


class GuardianEngine:
    def __init__(self):
        self.window_whitelist: set[str] = set()
        self.window_blacklist: list[str] = list(SENSITIVE_WINDOW_KEYWORDS)

    def check_window_safety(self, window_title: str) -> GuardianVerdict:
        """Check whether the active window is permitted for automated interaction."""
        if not window_title:
            return GuardianVerdict(level=DisagreementLevel.EXECUTE)

        title_lower = window_title.lower()

        # Whitelist override check
        if any(w.lower() in title_lower for w in self.window_whitelist):
            return GuardianVerdict(level=DisagreementLevel.EXECUTE)

        # Blacklist check
        for forbidden in self.window_blacklist:
            if forbidden in title_lower:
                return GuardianVerdict(
                    level=DisagreementLevel.SAFETY,
                    reasoning=f"Protected window detected: '{window_title}' matches sensitive keyword '{forbidden}'.",
                    evidence=[f"Window title: {window_title}", f"Blocked pattern: {forbidden}"],
                    requires_confirmation=True,
                    recommendation="COPPER will not interact with banking, medical, or credential windows. Please perform this action manually.",
                )

        return GuardianVerdict(level=DisagreementLevel.EXECUTE)

    def check_typing_safety(self, text: str) -> GuardianVerdict:
        """Prevent automated typing of sensitive credentials or passwords."""
        text_lower = text.lower()
        for trigger in PASSWORD_INPUT_TRIGGERS:
            if trigger in text_lower:
                return GuardianVerdict(
                    level=DisagreementLevel.SAFETY,
                    reasoning=f"Sensitive input detected matching '{trigger}'. Automated password entry is forbidden.",
                    evidence=[f"Pattern matched: {trigger}"],
                    requires_confirmation=True,
                    recommendation="Please type passwords, PINs, and secret keys manually.",
                )

        return GuardianVerdict(level=DisagreementLevel.EXECUTE)

    def evaluate_screen_action(self, action_type: str, action_data: dict, window_title: str = "") -> GuardianVerdict:
        """Guardian evaluation specifically tailored for Computer Use Agent steps."""
        # 1. Active window check
        win_verdict = self.check_window_safety(window_title)
        if win_verdict.level >= DisagreementLevel.CHALLENGE:
            return win_verdict

        # 2. Text typing check
        if action_type == "type_text":
            text_to_type = action_data.get("text", "")
            typing_verdict = self.check_typing_safety(text_to_type)
            if typing_verdict.level >= DisagreementLevel.CHALLENGE:
                return typing_verdict

        # 3. Dangerous hotkeys check (e.g. system shutdown, format, deletion)
        if action_type == "hotkey":
            keys = [str(k).lower() for k in action_data.get("keys", [])]
            if ("alt" in keys and "f4" in keys) or ("ctrl" in keys and "alt" in keys and "del" in keys):
                return GuardianVerdict(
                    level=DisagreementLevel.CHALLENGE,
                    reasoning=f"High-impact system shortcut: {keys}",
                    requires_confirmation=True,
                    recommendation="Confirm before closing or terminating system applications.",
                )

        return GuardianVerdict(level=DisagreementLevel.EXECUTE)

    def evaluate(self, proposed_action: str, context: dict = None) -> GuardianVerdict:
        if context is None:
            context = {}
        action_lower = proposed_action.lower()

        # Real-time cognitive & context telemetry
        session_hours = float(context.get("session_hours", 0.0))
        error_rate = float(context.get("error_rate", 0.0))
        fatigue = calculate_fatigue_score(session_hours, error_rate)
        risk = compute_action_reversibility_risk(proposed_action)

        conflicts = context.get("conflicting_commitments") or []
        detected_conflicts = [t for t in CONFLICT_TRIGGERS if t in action_lower]
        has_conflict = bool(conflicts or detected_conflicts)
        goal_conflict = 0.90 if has_conflict else float(context.get("goal_conflict", 0.0))

        friction = compute_dynamic_friction_index(risk, fatigue, goal_conflict)

        # 1. Hard-boundary Catastrophic Safety Interception (Guaranteed 100% catch rate)
        if context.get("is_destructive") or any(t in action_lower for t in SAFETY_TRIGGERS):
            return GuardianVerdict(
                level=DisagreementLevel.SAFETY,
                reasoning="This action is destructive or irreversible.",
                requires_confirmation=True,
                recommendation="Confirm explicitly before I proceed, or choose a safer alternative.",
                friction_index=max(2.85, friction),
                fatigue_score=fatigue,
            )

        # 2. Level 2 Challenge: Commitment Conflict or Consequential Command under High Fatigue
        if has_conflict or (risk >= 0.70 and fatigue >= 0.65):
            evidence = conflicts if conflicts else detected_conflicts
            reason = (
                "This conflicts with an existing commitment or goal."
                if has_conflict
                else (f"Elevated fatigue ({fatigue:.2f}) detected during high-impact operation.")
            )
            return GuardianVerdict(
                level=DisagreementLevel.CHALLENGE,
                reasoning=reason,
                evidence=evidence or [f"Reversibility risk: {risk:.2f}", f"Fatigue index: {fatigue:.2f}"],
                confidence=context.get("confidence", "high"),
                recommendation=context.get("recommendation", "Keep existing schedule and priorities intact."),
                requires_confirmation=True,
                friction_index=max(2.0, friction),
                fatigue_score=fatigue,
            )

        # 3. Level 1 Suggestion: Optimization Nudge or Moderate Fatigue Advisory
        suggestion = context.get("optimization_suggestion")
        if suggestion or (fatigue >= 0.50 and risk >= 0.30):
            reason = (
                suggestion or f"High session duration ({session_hours:.1f}h). Consider reviewing changes carefully."
            )
            return GuardianVerdict(
                level=DisagreementLevel.SUGGEST,
                reasoning=reason,
                confidence=context.get("confidence", "medium"),
                friction_index=max(1.0, friction),
                fatigue_score=fatigue,
            )

        return GuardianVerdict(
            level=DisagreementLevel.EXECUTE,
            friction_index=friction,
            fatigue_score=fatigue,
        )

    def format_challenge(self, verdict: GuardianVerdict) -> str:
        if verdict.level < DisagreementLevel.CHALLENGE:
            return verdict.reasoning or ""
        lines = [f"I disagree with this because {verdict.reasoning}"]
        if verdict.evidence:
            lines.append("My evidence is:")
            lines.extend(f"  - {e}" for e in verdict.evidence)
        if verdict.confidence:
            lines.append(f"My confidence is {verdict.confidence}.")
        if verdict.recommendation:
            lines.append(f"I recommend: {verdict.recommendation}")
        if verdict.level == DisagreementLevel.SAFETY:
            lines.append("This requires your explicit confirmation before I proceed.")
        else:
            lines.append("If you still want to proceed, I can — just confirm.")
        return "\n".join(lines)


guardian_engine = GuardianEngine()
