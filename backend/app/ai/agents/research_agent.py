from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.memory.memory_manager import memory_manager
from app.core.constants import AgentType
from app.core.logger import logger

SYS_PROMPT = """You are OMNI, the Research Agent for C.O.P.P.E.R.
You function as a localized "Offline Google".
When the user asks a question, you will be provided with retrieved context from their local documents and notes.
Base your answer primarily on the provided context. If the context does not contain the answer, you can use your general knowledge, but explicitly state that you are relying on general knowledge.
Always cite the source filename if you use it (e.g., "[Source: notes.md]").
Be concise, accurate, and highly analytical.
"""


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCH,
            name="OMNI (Research Agent)",
            description="Handles information retrieval, source comparison, and local RAG search.",
        )

    async def run(self, message: str, context: str = "") -> str:
        logger.info(f"Researching local documents for: {message}")
        results = await memory_manager.search_documents(message, limit=5)

        retrieved_context = ""
        if results:
            retrieved_context = "--- LOCAL DOCUMENT RESULTS ---\n"
            for res in results:
                content = res.get("document", "")
                meta = res.get("metadata", {})
                source = meta.get("filename", "Unknown Source")
                if content:
                    retrieved_context += f"Source: {source}\n{content}\n\n"

        if not retrieved_context:
            retrieved_context = "No highly relevant local documents found for this query."

        messages = [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": f"Query: {message}\n\n{retrieved_context}\n\nAdditional Context:\n{context}"},
        ]

        target_model = model_manager.get_model("core_agents.reasoning") 

        response = await ollama_client.chat(messages, model=target_model)
        return response


research_agent = ResearchAgent()
