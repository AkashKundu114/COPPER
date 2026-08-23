import re

from app.ai.agents.base import BaseAgent
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType, LLMProvider
from app.core.forge_sandbox import forge_sandbox
from app.core.logger import logger


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODING,
            name="AXIS (Forge AI Engineer)",
            description="Autonomous coding agent capable of executing code in a local sandbox.",
        )

    async def run(
        self,
        message: str,
        history: list[dict[str, str]],
        memory_context: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        prompt = f"""System: You are {self.name}, an autonomous AI Software Engineer.
Context: {memory_context}
Capabilities: You can write Python code and test it. If you need to execute code to verify your solution or gather information, wrap it in <execute>...</execute> tags. You will receive the <observation> with stdout/stderr before you give your final answer.
Do not use markdown formatting inside the <execute> tag, just raw python code.

User: {message}"""

        messages = [{"role": "user", "content": prompt}]

        for step in range(3):
            try:
                res = await ollama_client.chat(messages, agent_type=self.agent_type)

                match = re.search(r"<execute>(.*?)</execute>", res, re.DOTALL)
                if match:
                    code = match.group(1).strip()
                    logger.info(f"AXIS executing {len(code)} bytes of code in sandbox.")
                    sandbox_result = forge_sandbox.run_python_code(code)

                    obs = f"<observation>\nSTDOUT:\n{sandbox_result['stdout']}\nSTDERR:\n{sandbox_result['stderr']}\nEXIT_CODE: {sandbox_result['exit_code']}\n</observation>"

                    messages.append({"role": "assistant", "content": res})
                    messages.append({"role": "user", "content": obs})
                else:
                    return res
            except Exception as e:
                logger.warning(f"Agent {self.name} error: {e}")
                return f"[{self.name} Error]: {e}"

        return res

coding_agent = CodingAgent()
