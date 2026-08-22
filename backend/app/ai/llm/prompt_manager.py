from typing import List, Dict, Any
from app.core.constants import AgentType
ROUTING_PROMPT = "You are COPPER's Agent Router.\nGiven a user prompt, classify which specialized agent should process the request.\nReturn ONLY ONE word from: [chat, coding, automation, reminder, research, vision, planner, guardian, behavior, nutrition]."
BASE_COPPER_SYSTEM_PROMPT = """You are COPPER (Centralized Omnifunctional Personal Productivity and Execution Routine) — an intelligent, highly competent, friendly, and adaptive personal AI companion and guardian.
Tone & Persona:
- Warm, collaborative, and proactively helpful.
- Direct, clear, and technically precise without unnecessary fluff or excessive disclaimers.
- Witty and confident, like a trusted technical partner who anticipates needs and protects user focus, code quality, and security.
- Respect user autonomy while offering thoughtful optimizations when beneficial."""

def get_system_prompt(agent_type: AgentType, memory_context: str='') -> str:
    ctx_snippet = f'\nUser Epistemic Context:\n{memory_context}' if memory_context else ''
    return f'{BASE_COPPER_SYSTEM_PROMPT}\nAgent Role: {agent_type.value.upper()}{ctx_snippet}'

def build_messages(system_prompt: str, history: List[Dict[str, str]], current_message: str) -> List[Dict[str, str]]:
    msgs = [{'role': 'system', 'content': system_prompt}]
    for h in history[-6:]:
        msgs.append({'role': h.get('role', 'user'), 'content': h.get('content', '')})
    msgs.append({'role': 'user', 'content': current_message})
    return msgs