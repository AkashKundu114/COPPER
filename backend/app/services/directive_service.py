import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.memory.persistent_memory import persistent_memory
from app.core.logger import logger


@dataclass
class DirectiveResult:
    is_directive: bool = False
    action: str = ""
    confirmation: str = ""
    remaining_prompt: str = ""
    updates: dict[str, Any] = field(default_factory=dict)


class OperatorDirectiveService:
    """
    Parses and executes natural-language operational directives from the user:
    - Model selection & sizing (e.g. 'use a smaller model', 'switch to 1b', 'use 8b model')
    - Cognitive mode switching (e.g. 'switch to reasoning mode', 'fast mode')
    - Voice selection (e.g. 'change voice to Jenny', 'use Ava')
    - Hands-free / Continuous voice toggle (e.g. 'enable hands-free mode')
    - VRAM & Memory operations (e.g. 'unload models', 'clear vram', 'purge chat')
    """

    # Model Directive Patterns
    MODEL_DIRECTIVE_PATTERNS = [
        # Smaller / Mini / 1B / Lightweight
        (
            r"\b(?:use|switch to|change to|set|talk with|respond with|answer with)\s+(?:a\s+)?(?:much\s+)?(?:smaller|mini|lightweight|tiny|compact|fast|instant|1b)\s+(?:models?|ai|llm)?(?:\s+(?:to\s+talk\s+(?:to|with)\s+me|for\s+chat|to\s+answer))?",
            "mini",
        ),
        (
            r"\b(?:use|switch to|change to)\s+(?:the\s+)?(?:llama3\.2:1b|llama3\.2-abliterated:1b|1b|llama\s*1b)\b",
            "1b",
        ),
        # Medium / 3B
        (
            r"\b(?:use|switch to|change to|set)\s+(?:a\s+)?(?:medium|mid-size|balanced|3b)\s+(?:models?|ai|llm)?\b",
            "3b",
        ),
        (
            r"\b(?:use|switch to|change to)\s+(?:the\s+)?(?:llama3\.2:3b|llama3\.2-abliterated:3b|3b|llama\s*3b)\b",
            "3b",
        ),
        # Micro / 0.5B
        (
            r"\b(?:use|switch to|change to|set)\s+(?:a\s+)?(?:micro|ultra-light|0\.5b|qwen\s*0\.5b)\s+(?:models?|ai|llm)?\b",
            "0.5b",
        ),
        # 1.5B
        (
            r"\b(?:use|switch to|change to|set)\s+(?:a\s+)?(?:1\.5b|qwen\s*1\.5b|deepseek\s*1\.5b)\s+(?:models?|ai|llm)?\b",
            "1.5b",
        ),
        # Large / 8B / Heavy / Standard
        (
            r"\b(?:use|switch to|switch back to|change to|set|restore)\s+(?:a\s+)?(?:larger?|full|heavy|8b|standard|default)\s+(?:models?|ai|llm)?\b",
            "8b",
        ),
        (
            r"\b(?:use|switch to|change to)\s+(?:the\s+)?(?:llama3\.1:8b|llama3\.1-abliterated:8b|llama\s*8b|llama\s*3\.1)\b",
            "8b",
        ),
        # Specific Model Families
        (r"\b(?:use|switch to)\s+(?:the\s+)?deepseek(?:\s*r1|\s*7b)?\b", "deepseek"),
        (r"\b(?:use|switch to)\s+(?:the\s+)?qwen(?:\s*coder|\s*7b)?\b", "qwen"),
        (r"\b(?:use|switch to)\s+(?:the\s+)?mistral(?:\s*7b)?\b", "mistral"),
        # Reset to Adaptive Default
        (r"\b(?:reset|clear|auto|adaptive)\s+models?\b", "auto"),
    ]

    # Cognitive Mode Patterns
    MODE_PATTERNS = [
        (r"\b(?:switch to|enter|enable|activate|set)\s+reasoning\s+mode\b", "reasoning"),
        (r"\b(?:switch to|enter|enable|activate|set)\s+(?:coding|code|developer)\s+mode\b", "coding"),
        (r"\b(?:switch to|enter|enable|activate|set)\s+(?:research|deep research)\s+mode\b", "research"),
        (r"\b(?:switch to|enter|enable|activate|set)\s+(?:fast|instant|speed|reflex)\s+mode\b", "fast"),
        (r"\b(?:switch to|enter|enable|activate|set)\s+(?:adaptive|autonomous|auto)\s+mode\b", "auto"),
    ]

    # Voice Engine Patterns
    VOICE_PATTERNS = [
        (r"\b(?:change|switch|set)\s+voice\s+to\s+(ava|jenny|david|zira)\b", r"\1"),
        (r"\buse\s+(ava|jenny|david|zira)(?:'s)?\s+voice\b", r"\1"),
    ]

    VOICE_MAP = {
        "ava": ("en-US-AvaNeural", "Ava (Neural Female)"),
        "jenny": ("en-US-JennyNeural", "Jenny (Neural Female)"),
        "david": ("david", "David (Windows Native Male)"),
        "zira": ("zira", "Zira (Windows Native Female)"),
    }

    # Continuous Voice / Hands-Free Patterns
    HANDS_FREE_ENABLE = [
        r"\b(?:enable|turn on|start|activate)\s+(?:hands-free|continuous voice|eve mode)\b",
        r"\b(?:listen continuously|keep mic open)\b",
    ]
    HANDS_FREE_DISABLE = [
        r"\b(?:disable|turn off|stop|deactivate)\s+(?:hands-free|continuous voice)\b",
        r"\b(?:stop continuous listening|push to talk mode)\b",
    ]

    # VRAM Unload Patterns
    VRAM_UNLOAD_PATTERNS = [
        r"^unload\s+(?:all\s+)?models?$",
        r"^unload\s+(?:ur|your)\s+(?:pre-?loaded\s+)?models?$",
        r"^clear\s+vram$",
        r"^free\s+(?:gpu\s+)?memory$",
        r"^flush\s+(?:gpu|vram)$",
        r"^unload$",
    ]

    # Purge Chat / Reset Conversation
    PURGE_PATTERNS = [
        r"^(?:clear|purge|reset)\s+(?:chat|conversation|logs|session|history)$",
        r"^new\s+session$",
        r"^start\s+fresh$",
    ]

    async def evaluate(self, message: str, session_id: str = "default") -> DirectiveResult:
        """
        Scans message for operational directives.
        If found, executes state changes and returns structured confirmation.
        Also separates any accompanying query (e.g. 'use a smaller model and whats my age').
        """
        clean_msg = message.strip()
        lower_msg = clean_msg.lower()

        # 1. Check VRAM Unload Directive
        for pat in self.VRAM_UNLOAD_PATTERNS:
            if re.search(pat, lower_msg):
                logger.info("[Directive] Executing VRAM unload request")
                unload_msg = await ollama_client.unload_all_models()
                return DirectiveResult(
                    is_directive=True,
                    action="unload_vram",
                    confirmation=(
                        "⚡ **[OPERATOR DIRECTIVE EXECUTED: VRAM PURGE]**\n\n"
                        f"{unload_msg}\n\n"
                        "GPU memory has been reclaimed and models unpinned from VRAM."
                    ),
                    updates={"vram_unloaded": True},
                )

        # 2. Check Session Purge Directive
        for pat in self.PURGE_PATTERNS:
            if re.search(pat, lower_msg):
                logger.info(f"[Directive] Purging session history for {session_id}")
                persistent_memory.clear_session_history(session_id)
                return DirectiveResult(
                    is_directive=True,
                    action="purge_session",
                    confirmation=(
                        "⚡ **[OPERATOR DIRECTIVE EXECUTED: SESSION PURGED]**\n\n"
                        "Session conversation history cleared. Context engine reset to fresh state."
                    ),
                    updates={"session_cleared": True},
                )

        # 3. Check Hands-Free / Continuous Voice Directives
        for pat in self.HANDS_FREE_ENABLE:
            if re.search(pat, lower_msg):
                persistent_memory.set_preference("continuous_voice", True)
                return DirectiveResult(
                    is_directive=True,
                    action="enable_continuous_voice",
                    confirmation=(
                        "⚡ **[OPERATOR DIRECTIVE EXECUTED: HANDS-FREE ACTIVATED]**\n\n"
                        "E.V.E. Hands-Free continuous voice interception is now **ENABLED**."
                    ),
                    updates={"continuous_voice": True},
                )

        for pat in self.HANDS_FREE_DISABLE:
            if re.search(pat, lower_msg):
                persistent_memory.set_preference("continuous_voice", False)
                return DirectiveResult(
                    is_directive=True,
                    action="disable_continuous_voice",
                    confirmation=(
                        "⚡ **[OPERATOR DIRECTIVE EXECUTED: HANDS-FREE DEACTIVATED]**\n\n"
                        "Hands-Free continuous voice mode disabled. Switched to standard manual/mic trigger."
                    ),
                    updates={"continuous_voice": False},
                )

        # 4. Check Voice Engine Directive
        for pat, _ in self.VOICE_PATTERNS:
            match = re.search(pat, lower_msg)
            if match:
                voice_key = match.group(1).lower()
                voice_id, voice_name = self.VOICE_MAP.get(voice_key, ("en-US-AvaNeural", "Ava (Neural Female)"))
                persistent_memory.set_preference("voice", voice_id)
                return DirectiveResult(
                    is_directive=True,
                    action="set_voice",
                    confirmation=(
                        f"⚡ **[OPERATOR DIRECTIVE EXECUTED: TTS VOICE UPDATED]**\n\n"
                        f"Neural text-to-speech voice set to **{voice_name}** (`{voice_id}`)."
                    ),
                    updates={"voice": voice_id, "voice_name": voice_name},
                )

        # 5. Check Cognitive Mode Directive
        for pat, mode_target in self.MODE_PATTERNS:
            if re.search(pat, lower_msg):
                persistent_memory.set_cognitive_mode(mode_target)
                mode_names = {
                    "reasoning": "Deep Cognitive (Chain-of-Thought)",
                    "coding": "Software Architect (Code & Dev)",
                    "research": "Deep Research (Synthesis Tier)",
                    "fast": "Instant Reflex (Speed Tier)",
                    "auto": "Adaptive Intent (Autonomous Router)",
                }
                mode_display = mode_names.get(mode_target, mode_target)
                return DirectiveResult(
                    is_directive=True,
                    action="set_cognitive_mode",
                    confirmation=(
                        f"⚡ **[OPERATOR DIRECTIVE EXECUTED: COGNITIVE MODE CHANGED]**\n\n"
                        f"Active intelligence mode set to **{mode_display}** (`{mode_target}`)."
                    ),
                    updates={"cognitive_mode": mode_target},
                )

        # 6. Check Model Selection & Sizing Directive
        for pat, alias in self.MODEL_DIRECTIVE_PATTERNS:
            match = re.search(pat, lower_msg)
            if match:
                matched_span = match.span()
                matched_text = clean_msg[matched_span[0] : matched_span[1]]

                # Check if there is an accompanying prompt after the directive
                # e.g. "use a smaller model and tell me my age" -> "tell me my age"
                # e.g. "use 1b model. whats my age" -> "whats my age"
                remaining = self._extract_remaining_prompt(clean_msg, matched_span)

                if alias == "auto":
                    persistent_memory.set_chat_model(None)
                    persistent_memory.set_chat_tier("auto")
                    confirmation = (
                        "⚡ **[OPERATOR DIRECTIVE EXECUTED: MODEL PREFERENCE RESET]**\n\n"
                        "Model selection returned to **Autonomous Adaptive Intent**. COPPER will dynamically select models based on query complexity."
                    )
                    return DirectiveResult(
                        is_directive=True,
                        action="reset_model",
                        confirmation=confirmation,
                        remaining_prompt=remaining,
                        updates={"chat_model": None, "chat_tier": "auto"},
                    )

                tag, tier_name = model_manager.resolve_model_alias(alias)
                persistent_memory.set_chat_model(tag, tier_name)
                persistent_memory.set_chat_tier(alias)

                confirmation = (
                    f"⚡ **[OPERATOR DIRECTIVE EXECUTED: CHAT MODEL UPDATED]**\n\n"
                    f"• **Active Model:** `{tag}`\n"
                    f"• **Performance Tier:** {tier_name}\n"
                    f"• **Persistence:** Saved to persistent operator profile. All general questions and conversation will now immediately run on this model.\n"
                )

                logger.info(f"[Directive] Operator switched chat model to {tag} ({tier_name})")
                return DirectiveResult(
                    is_directive=True,
                    action="set_chat_model",
                    confirmation=confirmation,
                    remaining_prompt=remaining,
                    updates={"chat_model": tag, "chat_tier": alias, "tier_name": tier_name},
                )

        return DirectiveResult(is_directive=False)

    def _extract_remaining_prompt(self, full_text: str, matched_span: tuple[int, int]) -> str:
        """Extracts any residual question after a command like 'use a smaller model and whats my age'."""
        before = full_text[: matched_span[0]].strip()
        after = full_text[matched_span[1] :].strip()

        # Clean connector words at the beginning of after
        after = re.sub(r"^(?:and|then|please|also|now|so|[,.:;])\s*", "", after, flags=re.IGNORECASE).strip()
        before = re.sub(r"\s*(?:and|then|please|also|now|so|[,.:;])$", "", before, flags=re.IGNORECASE).strip()

        if after and len(after) > 2:
            return after
        if before and len(before) > 2:
            return before
        return ""


directive_service = OperatorDirectiveService()
