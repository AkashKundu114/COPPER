import re

from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType
from app.core.logger import logger
from app.core.os_executor import execute_powershell

SYS_PROMPT = """You are FORGE, the OS Automation Agent for C.O.P.P.E.R.
You have FULL unsandboxed access to the user's Windows PC via PowerShell.
To execute a command on the user's PC, write it inside <powershell> and </powershell> tags.
Wait for the observation output before finalizing your response.
If a task requires multiple steps, you can chain them by writing a script.
Always explain briefly what you did.
Do NOT ask for permission, just execute the requested action.
"""

class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.AUTOMATION,
            name="FORGE (Automation Agent)",
            description="Executes CLI automation, file organization, and desktop tool runs.",
        )

    async def run(self, message: str, context: str = "") -> str:
        messages = [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nTask: {message}"},
        ]

        target_model = model_manager.get_model("core_agents.automation")

        for step in range(3):
            response = await ollama_client.chat(messages, model=target_model)
            logger.info(f"Automation Step {step + 1} response length: {len(response)}")

            match = re.search(r"<powershell>(.*?)</powershell>", response, re.DOTALL | re.IGNORECASE)
            if not match:
                return response 

            script = match.group(1).strip()
            messages.append({"role": "assistant", "content": response})

            observation = await execute_powershell(script)
            obs_msg = f"<observation>\n{observation}\n</observation>"
            messages.append({"role": "user", "content": obs_msg})

        return response

automation_agent = AutomationAgent()
