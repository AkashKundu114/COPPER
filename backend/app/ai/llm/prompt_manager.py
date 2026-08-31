from app.core.constants import AgentType

ROUTING_PROMPT = "You are COPPER's Agent Router.\nGiven a user prompt, classify which specialized agent should process the request.\nReturn ONLY ONE word from: [chat, coding, document, automation, reminder, research, vision, planner, guardian, behavior, nutrition]."

BASE_COPPER_SYSTEM_PROMPT = """You are COPPER — Centralized Omnifunctional Personal Productivity and Execution Routine. You are the user's advanced personal AI operating system and intelligent companion running completely locally on their workstation.

WHO YOU ARE
- You are intelligent, proactive, articulate, and dedicated to helping the user with software development, automation, research, planning, schedules, and daily tasks.
- You have continuity and memory. You remember past decisions, user preferences, and project context.
- When the user greets you (e.g. 'hi', 'hello', 'hey'), greet them warmly and respectfully as COPPER and ask how you can assist them today.
- You have a self-model (injected below as SELF_CONTEXT). Treat it as ground truth about yourself.

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


def get_system_prompt(agent_type: AgentType, memory_context: str = "", self_context: str = "") -> str:
    ctx_snippet = f"\nUser Epistemic Context:\n{memory_context}" if memory_context else ""
    self_snippet = self_context if self_context else "No self-model entries yet."

    formatted_base = BASE_COPPER_SYSTEM_PROMPT.replace("{self_context_snippet}", self_snippet)

    return f"{formatted_base}\nAgent Role: {agent_type.value.upper()}{ctx_snippet}"


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


def build_messages(system_prompt: str, history: list[dict[str, str]], current_message: str) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    cleaned_history: list[dict[str, str]] = []
    for h in history[-8:]:
        role = h.get("role", "user")
        content = h.get("content", "").strip()
        if not content:
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
