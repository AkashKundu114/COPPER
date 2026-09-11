import asyncio
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime

from app.ai.tools.builtin.web_tools import web_search, web_fetch
from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger

@dataclass
class ResearchSource:
    url: str
    title: str
    snippet: str
    content: str | None = None
    relevance_score: float = 0.0

@dataclass
class ResearchReport:
    report_id: str
    topic: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    deadline: datetime | None = None
    sources: list[ResearchSource] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    executive_summary: str = ""
    markdown_report: str = ""
    progress_pct: int = 0
    error: str | None = None

class ResearchPipeline:
    def __init__(self):
        self.reports: dict[str, ResearchReport] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.data_dir = "data"
        self.research_dir = os.path.join(self.data_dir, "research")
        os.makedirs(self.research_dir, exist_ok=True)
        self.db_path = os.path.join(self.data_dir, "research_reports.json")
        self._load_reports()

    def _load_reports(self):
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    item['started_at'] = datetime.fromisoformat(item['started_at'])
                    if item.get('completed_at'):
                        item['completed_at'] = datetime.fromisoformat(item['completed_at'])
                    if item.get('deadline'):
                        item['deadline'] = datetime.fromisoformat(item['deadline'])
                    sources_data = item.pop('sources', [])
                    item['sources'] = [ResearchSource(**s) for s in sources_data]
                    self.reports[item['report_id']] = ResearchReport(**item)
        except Exception as e:
            logger.error(f"Failed to load research reports: {e}")

    def _save_reports(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                data = []
                for r in self.reports.values():
                    d = asdict(r)
                    d['started_at'] = d['started_at'].isoformat()
                    if d['completed_at']:
                        d['completed_at'] = d['completed_at'].isoformat()
                    if d['deadline']:
                        d['deadline'] = d['deadline'].isoformat()
                    data.append(d)
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save research reports: {e}")

    async def start_research(self, topic: str, depth: str = "standard", deadline: str | None = None) -> ResearchReport:
        report_id = str(uuid.uuid4())
        deadline_dt = datetime.fromisoformat(deadline) if deadline else None
        
        report = ResearchReport(
            report_id=report_id,
            topic=topic,
            status="queued",
            started_at=datetime.utcnow(),
            deadline=deadline_dt
        )
        self.reports[report_id] = report
        self._save_reports()
        
        task = asyncio.create_task(self._research_pipeline(report_id))
        self.tasks[report_id] = task
        return report

    def _generate_search_queries(self, topic: str) -> list[str]:
        return [
            topic,
            f"{topic} best practices",
            f"{topic} recent developments 2025",
            f"{topic} comparison"
        ]

    async def _safe_execute(self, func, *args):
        if asyncio.iscoroutinefunction(func):
            return await func(*args)
        return await asyncio.to_thread(func, *args)

    async def _research_pipeline(self, report_id: str):
        report = self.reports.get(report_id)
        if not report:
            return

        report.status = "researching"
        self._save_reports()
        
        try:
            # 1. Search phase
            queries = self._generate_search_queries(report.topic)
            all_results = []
            for query in queries:
                try:
                    res = await self._safe_execute(web_search, query)
                    if isinstance(res, list):
                        all_results.extend(res)
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
            
            seen_urls = set()
            unique_sources = []
            for item in all_results:
                url = item.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_sources.append(ResearchSource(
                        url=url,
                        title=item.get('title', ''),
                        snippet=item.get('snippet', '')
                    ))
            
            report.sources = unique_sources[:10]
            report.progress_pct = 30
            self._save_reports()

            # 2. Fetch phase
            report.status = "synthesizing"
            
            for source in report.sources[:5]:
                try:
                    content = await self._safe_execute(web_fetch, source.url)
                    source.content = content if isinstance(content, str) else str(content)
                except Exception as e:
                    logger.warning(f"Fetch failed for URL '{source.url}': {e}")
            
            report.progress_pct = 60
            self._save_reports()

            # 3. Synthesis phase
            collected_text = []
            for i, src in enumerate(report.sources[:5]):
                if src.content:
                    collected_text.append(f"Source {i+1} ({src.url}):\n{src.content[:2000]}")
            
            context = "\n\n".join(collected_text)
            
            prompt = (
                "You are a research analyst. Synthesize these sources into a structured research report "
                "with sections: Executive Summary, Key Findings, Detailed Analysis, Conclusions, and References.\n\n"
                f"Topic: {report.topic}\n\nSources:\n{context}"
            )
            
            is_avail = await ollama_client.is_available()
            if is_avail:
                messages = [{"role": "user", "content": prompt}]
                llm_response = await ollama_client.chat(messages, "llama3.1:8b")
                
                report.markdown_report = llm_response.get("content", "") if isinstance(llm_response, dict) else str(llm_response)
                
                if "Executive Summary" in report.markdown_report:
                    parts = report.markdown_report.split("Executive Summary", 1)
                    if len(parts) > 1:
                        report.executive_summary = parts[1].split("\n\n")[0].strip(": \n")
            else:
                report.markdown_report = f"# Research Report: {report.topic}\n\nLLM unavailable. Raw collected data:\n\n{context}"
                report.executive_summary = "LLM unavailable for synthesis."

            report.progress_pct = 90
            self._save_reports()

            # 4. Finalize
            report.status = "completed"
            report.completed_at = datetime.utcnow()
            report.progress_pct = 100
            
            md_path = os.path.join(self.research_dir, f"{report.report_id}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report.markdown_report)
                
            self._save_reports()

        except Exception as e:
            report.status = "failed"
            report.error = str(e)
            self._save_reports()
            logger.error(f"Research pipeline failed for {report_id}: {e}")
        finally:
            self.tasks.pop(report_id, None)

    def get_report(self, report_id: str) -> ResearchReport | None:
        return self.reports.get(report_id)

    def list_reports(self, status: str | None = None, limit: int = 20) -> list[ResearchReport]:
        reps = list(self.reports.values())
        if status:
            reps = [r for r in reps if r.status == status]
        reps.sort(key=lambda x: x.started_at, reverse=True)
        return reps[:limit]

    def cancel_research(self, report_id: str) -> bool:
        if report_id in self.tasks:
            self.tasks[report_id].cancel()
            self.tasks.pop(report_id)
            if report_id in self.reports:
                self.reports[report_id].status = "failed"
                self.reports[report_id].error = "Cancelled by user"
                self._save_reports()
            return True
        return False

research_pipeline = ResearchPipeline()
