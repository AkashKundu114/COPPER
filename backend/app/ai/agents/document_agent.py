import json
import re
from collections.abc import AsyncGenerator

from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger
from app.services.document_service import document_service


class DocumentAgent(BaseAgent):
    """
    KINESIS (Document Architect and Synthesizer)
    Autonomous Document Generation Agent within C.O.P.P.E.R.
    Generates professional PDFs, Word DOCX, Markdown, HTML, CSV/TSV, and JSON files.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.DOCUMENT,
            name="KINESIS (Document Architect)",
            description="Autonomous document generation agent capable of synthesizing multi-format reports, proposals, tables, and documents.",
        )

    def _detect_format(self, prompt: str) -> str:
        p = prompt.lower()
        if "word" in p or ".docx" in p or "docx" in p or "ms word" in p:
            return "docx"
        elif "slide" in p or "presentation" in p or "pptx" in p or ".pptx" in p or "powerpoint" in p:
            return "pptx"
        elif "excel" in p or "xlsx" in p or ".xlsx" in p or "workbook" in p:
            return "xlsx"
        elif "markdown" in p or ".md" in p or "md file" in p:
            return "md"
        elif "html" in p or "webpage" in p or "web document" in p or ".html" in p:
            return "html"
        elif "csv" in p or "spreadsheet" in p or "excel sheet" in p or "comma separated" in p:
            return "csv"
        elif "tsv" in p or "tab separated" in p:
            return "tsv"
        elif "json" in p or "json data" in p:
            return "json"
        elif "yaml" in p or "yml" in p:
            return "yaml"
        elif "plain text" in p or "txt file" in p or ".txt" in p:
            return "txt"
        return "pdf"

    def _detect_template(self, prompt: str) -> str:
        p = prompt.lower()
        if "technical" in p or "architecture" in p or "system report" in p:
            return "technical_report"
        elif "proposal" in p or "pitch" in p or "business plan" in p:
            return "project_proposal"
        elif "executive" in p or "briefing" in p or "leadership" in p:
            return "executive_summary"
        elif "meeting" in p or "minutes" in p or "agenda" in p:
            return "meeting_notes"
        elif "resume" in p or "cv" in p or "curriculum vitae" in p:
            return "resume"
        elif "letter" in p or "formal letter" in p or "official letter" in p:
            return "formal_letter"
        elif "invoice" in p or "financial" in p or "expense" in p or "budget" in p or "table" in p:
            return "invoice_table"
        elif "research" in p or "paper" in p or "study" in p or "academic" in p:
            return "research_paper"
        return "technical_report"

    async def run(
        self,
        message: str,
        history: list[dict[str, str]],
        memory_context: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        format_detected = self._detect_format(message)
        template_detected = self._detect_template(message)

        target_model = model_manager.get_document_model()

        system_prompt = f"""You are {self.name}, the specialized Autonomous Document Architect for C.O.P.P.E.R.
Your goal is to author high-quality, professional, multi-section documents.

Target Document Format: {format_detected.upper()}
Document Template Archetype: {template_detected}

Context: {memory_context}

Respond in TWO parts:
1. First, an executive summary and brief explanation of what was composed.
2. Second, a JSON block enclosed in ```json ... ``` with this exact structure:
{{
  "title": "Document Title",
  "filename": "suggested_filename",
  "format": "{format_detected}",
  "template": "{template_detected}",
  "sections": [
    {{
      "heading": "Section Heading",
      "content": "Detailed paragraphs...",
      "bullets": ["Key point 1", "Key point 2"],
      "table": {{
        "headers": ["Col 1", "Col 2", "Col 3"],
        "rows": [
          ["Val 1", "Val 2", "Val 3"]
        ]
      }}
    }}
  ]
}}

Ensure content is rigorous, thorough, actionable, and formatted for direct publication."""

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]

        try:
            raw_response = await ollama_client.chat(messages, model=target_model)

            # Extract JSON block to build the actual file artifact
            json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_response)
            created_doc_meta = None

            if json_match:
                try:
                    doc_data = json.loads(json_match.group(1))
                    title = doc_data.get("title", "Generated Document")
                    sections = doc_data.get("sections", [])
                    fmt = doc_data.get("format", format_detected)
                    fname = doc_data.get("filename")

                    created_doc_meta = await document_service.create_document(
                        format=fmt,
                        title=title,
                        sections=sections,
                        raw_content=raw_response,
                        template_type=template_detected,
                        filename=fname,
                        author="C.O.P.P.E.R. AI",
                    )
                except Exception as parse_err:
                    logger.warning(f"Could not parse generated document JSON: {parse_err}")

            if not created_doc_meta:
                # Direct fallback creation using raw message text
                title_clean = re.sub(r"[^\w\s]", "", message[:40]).strip().title() or "AI Document"
                created_doc_meta = await document_service.create_document(
                    format=format_detected,
                    title=title_clean,
                    raw_content=raw_response,
                    template_type=template_detected,
                )

            summary_part = raw_response.split("```")[0].strip()
            if not summary_part:
                summary_part = f"I have composed and formatted your **{created_doc_meta['format'].upper()}** document: **{created_doc_meta['title']}**."

            doc_banner = (
                "\n\n📄 **Document Artifact Created Successfully**\n"
                f"- **Filename**: `{created_doc_meta['filename']}`\n"
                f"- **Format**: `{created_doc_meta['format'].upper()}` ({created_doc_meta['size_formatted']})\n"
                f"- **Template**: `{created_doc_meta['template_type'].replace('_', ' ').title()}`\n"
                f"- **Storage Path**: `{created_doc_meta['filepath']}`\n"
                f"- **Download URL**: [{created_doc_meta['filename']}]({created_doc_meta['download_url']})\n"
            )

            return f"{summary_part}{doc_banner}"

        except Exception as e:
            logger.error(f"DocumentAgent execution failed: {e}")
            # Resilient fallback creation
            fallback_meta = await document_service.create_document(
                format=format_detected,
                title="Generated Summary Document",
                raw_content=f"User Request: {message}\n\nDocument creation fallback generated.",
                template_type=template_detected,
            )
            return (
                f"Generated document artifact `{fallback_meta['filename']}` ({fallback_meta['format'].upper()}) "
                f"at `{fallback_meta['filepath']}`."
            )

    async def stream(
        self,
        message: str,
        history: list[dict[str, str]],
        memory_context: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        res = await self.run(message, history, memory_context, provider)
        yield res


document_agent = DocumentAgent()
