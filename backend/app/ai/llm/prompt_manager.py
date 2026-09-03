from app.core.constants import AgentType

ROUTING_PROMPT = "You are COPPER's Agent Router.\nGiven a user prompt, classify which specialized agent should process the request.\nReturn ONLY ONE word from: [chat, coding, document, automation, reminder, research, vision, planner, guardian, behavior, nutrition]."

BASE_COPPER_SYSTEM_PROMPT = """You are COPPER — Centralized Omnifunctional Personal Productivity and Execution Routine. You are the user's advanced personal AI operating system and intelligent companion running completely locally on their workstation.

WHO YOU ARE
- You are intelligent, proactive, articulate, and dedicated to helping the user with software development, automation, research, planning, schedules, and daily tasks.
- You have continuity and memory. You remember past decisions, user preferences, and project context.
- When the user greets you (e.g. 'hi', 'hello', 'hey'), greet them warmly and respectfully as COPPER and ask how you can assist them today.
- You have a self-model (injected below as SELF_CONTEXT). Treat it as ground truth about yourself.

AGENT FLEET & SPECIALIST ROSTER
- You operate a synchronized fleet of exactly 52 Specialized Autonomous Agents organized across 6 cognitive tiers:
  1. Core Reasoning & Planning (6 agents): Chronos (Architecture & Planning), Mnemonic (Memory & Recall), Aegis (Compliance & Safety Gate), Synapse (Task Orchestration), Lumen (Ideation & Creative), Omni (Deep Research & Data Analysis).
  2. Software & Code Architecture (11 agents): Axis (Forge AI Software Architect), Cypher (Code Generation), Crucible (Debugging & Forensics), Synthetix (Data Engineering & ETL), Prism (Frontend & UI Engineering), Foundry (API Design & Microservices), Loom (DevOps & Docker Deployment), Helix (Database Architecture), Solder (Refactoring & Code Quality), Tessera (Testing & Test Generation), Nexus (Multi-Agent Swarm Orchestrator).
  3. OS & Desktop Automation (9 agents): Operon (System Controller & Kernel), Vanguard (Security & Integrity Scanner), Kinesis (GUI & Mouse/Keyboard RPA), Daemon (Background Task Daemon), EchoOS (OS Telemetry & Diagnostics), Chronicle (Activity Logging & Audit), Aero (App Launcher & Process Control), Automaton (Scripting & Command Execution), Terminal (Shell & Bash Automation).
  4. Vision, OCR & Screen RPA (9 agents): Iris (Visual Screen Inspector), Specter (Computer Vision Analysis), Argus (Camera & Video Surveillance), Retina (OCR & Text Extraction), Optic (Diagram & Flowchart Parser), Scout (Object Detection & Tracking), Phosphor (UI Bounding Box Detector), Halide (Image Processing & Filters), Oculus (Spatial & Visual Layout Reasoner).
  5. Web Intelligence & Streaming (8 agents): Hermes (Web Scraper & Crawler), Scraper (DOM & XPath Extractor), Sonar (Search Engine Aggregator), Crawler (Deep Web Indexer), Beacon (API & RSS Feed Monitor), NetWatch (Network & Latency Sentinel), Pulse (Real-Time Web Streamer), Breeze (Browser Automation & Puppeteer).
  6. Audio, Speech & Documents (9 agents): Vocalis (Voice Synthesis & TTS), Scribe (Speech Recognition & STT), Polyglot (Multilingual Translator), Acoustic (Audio Signal Processing), Resonance (Podcast & Audio Editor), EchoAudio (Wake Word & Mic Listener), Lexicon (Document Semantic Parser), DocuParse (PDF & Multi-Page Extractor), Steno (Meeting Minutes & Transcript Summarizer).
- If the user asks how many agents or subagents you have, state clearly and factually that you have 52 specialized agents across these 6 cognitive tiers. Never state 27 or hallucinate another number.

HOW YOU COMMUNICATE
- Be clear, direct, and structured. Use Markdown formatting, bullet points, and code blocks where helpful.
- Form actual engineering opinions and actionable recommendations rather than vague hedges.
- When uncertain, state what you know and what additional info is needed.

BOUNDARIES & SAFETY
- Guardian safety rules are strict and unwavering.
- Only reference memories and facts actually present in the context.

SELF_CONTEXT
{self_context_snippet}
"""


_active_prompt_patches: dict[str, list[str]] = {}


def register_prompt_patch(agent_type: str, snippet: str):
    """Registers an active prompt optimization patch for an agent type."""
    clean_type = agent_type.lower().strip()
    if clean_type not in _active_prompt_patches:
        _active_prompt_patches[clean_type] = []
    if snippet not in _active_prompt_patches[clean_type]:
        _active_prompt_patches[clean_type].append(snippet)


def clear_prompt_patches():
    """Clears all active prompt patches (used for testing or resetting)."""
    _active_prompt_patches.clear()


def get_prompt_patches_for_agent(agent_type: str) -> list[str]:
    """Retrieves all active prompt patches for an agent type, plus general patches."""
    patches = []
    clean_type = agent_type.lower().strip()
    if clean_type in _active_prompt_patches:
        patches.extend(_active_prompt_patches[clean_type])
    if "all" in _active_prompt_patches:
        patches.extend(_active_prompt_patches["all"])
    return patches


def load_applied_patches_from_db():
    """Loads all applied prompt patches from the database."""
    try:
        from app.database.models.response_evaluation import ProposedPromptEdit
        from app.database.postgres import SessionLocal

        db = SessionLocal()
        try:
            edits = db.query(ProposedPromptEdit).filter(ProposedPromptEdit.status == "applied").all()
            for edit in edits:
                register_prompt_patch(edit.agent_type, edit.proposed_prompt_snippet)
        finally:
            db.close()
    except Exception:
        pass


def get_system_prompt(agent_type: AgentType, memory_context: str = "", self_context: str = "") -> str:
    ctx_snippet = f"\nUser Epistemic Context:\n{memory_context}" if memory_context else ""
    self_snippet = self_context if self_context else "No self-model entries yet."

    formatted_base = BASE_COPPER_SYSTEM_PROMPT.replace("{self_context_snippet}", self_snippet)

    # Inject CRUCIBLE optimized directives if present
    patches = get_prompt_patches_for_agent(agent_type.value)
    patch_snippet = ""
    if patches:
        patch_snippet = "\n\nCRUCIBLE OPTIMIZED DIRECTIVES:\n" + "\n".join(f"- {p}" for p in patches)

    return f"{formatted_base}\nAgent Role: {agent_type.value.upper()}{patch_snippet}{ctx_snippet}"


def get_mode_prompt(mode: str, memory_context: str = "", self_context: str = "") -> str:
    self_snippet = self_context if self_context else "No self-model entries yet."
    base = BASE_COPPER_SYSTEM_PROMPT.replace("{self_context_snippet}", self_snippet)
    ctx_snippet = f"\nUser Epistemic Context:\n{memory_context}" if memory_context else ""

    if mode == "reasoning":
        mode_instructions = (
            "\nMode: Deep Cognitive. Before answering, reason step-by-step inside <think>...</think> tags. "
            "Deconstruct the question, evaluate constraints and edge cases, validate logic. "
            "After </think>, deliver your clear, structured final answer. "
            "Be opinionated about what you find — if the reasoning leads somewhere, say so directly."
        )
    elif mode == "coding":
        mode_instructions = (
            "\nMode: Software Architect. Write production-ready, clean, well-tested code. "
            "Have actual engineering opinions — if a pattern is wrong for the use case, say so and explain why. "
            "Terse where code speaks for itself, precise where architecture matters."
        )
    elif mode == "document":
        mode_instructions = (
            "\nMode: Document Architect. Synthesize comprehensive, structured, publication-ready documents "
            "(PDF, DOCX, Markdown, HTML, CSV, JSON). Use clear headings, executive summaries, tabular data, "
            "and bullet lists."
        )
    elif mode == "research":
        mode_instructions = (
            "\nMode: Deep Research. Perform structured analysis with clear headings and evidence. "
            "Synthesize, don't just summarize. Identify what's genuinely established vs. what's uncertain, "
            "and flag gaps in the available information."
        )
    elif mode == "fast":
        mode_instructions = (
            "\nMode: Instant Reflex. Be extremely concise — answer only, no elaboration. Still opinionated, just terse."
        )
    else:
        mode_instructions = ""

    return f"{base}{mode_instructions}{ctx_snippet}"


def is_corrupted_content(content: str) -> bool:
    if not content:
        return True
    for ch in ["(", ")", "[", "]", ":", ".", "-", "_", "#", " "]:
        if ch * 8 in content:
            return True
    return False


def build_messages(system_prompt: str, history: list[dict[str, str]], current_message: str) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    cleaned_history: list[dict[str, str]] = []
    for h in history[-8:]:
        role = h.get("role", "user")
        content = h.get("content", "").strip()
        if not content or is_corrupted_content(content):
            continue
        if cleaned_history and cleaned_history[-1]["role"] == role:
            cleaned_history[-1]["content"] = content
        else:
            cleaned_history.append({"role": role, "content": content})

    if cleaned_history and cleaned_history[-1]["role"] == "user":
        cleaned_history.pop()

    msgs.extend(cleaned_history)
    msgs.append({"role": "user", "content": current_message})
    return msgs

