import csv
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import httpx

from app.ai.tools.registry import tool_registry
from app.core.logger import logger


@tool_registry.tool(
    name="arxiv_search",
    description="Search research preprints on arXiv by topic, keywords, or authors via the official arXiv API.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query terms (e.g., 'quantum error correction', 'transformer pruning').",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of papers to return (default: 5).",
            },
        },
        "required": ["query"],
    },
    return_description="List of academic papers with title, authors, abstract, arXiv ID, and PDF URL.",
    guardian_level=0,
)
async def arxiv_search(query: str, max_results: int = 5) -> dict[str, Any]:
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(max_results, 20),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)

        if resp.status_code != 200:
            return {"status": "error", "error": f"arXiv API error: HTTP {resp.status_code}"}

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            id_tag = entry.find("atom:id", ns)

            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
                if author.find("atom:name", ns) is not None
            ]

            pdf_link = None
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    pdf_link = link.attrib.get("href")

            entries.append({
                "title": title.text.strip().replace("\n", " ") if title is not None else "Untitled",
                "authors": authors[:5],
                "published": published.text[:10] if published is not None else None,
                "arxiv_id": id_tag.text.split("/abs/")[-1] if id_tag is not None else None,
                "pdf_url": pdf_link,
                "abstract": summary.text.strip()[:600] + "..." if summary is not None else "",
            })

        return {
            "status": "success",
            "query": query,
            "total_found": len(entries),
            "papers": entries,
        }
    except Exception as e:
        logger.error(f"arxiv_search error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="dataset_summary",
    description="Compute offline descriptive statistics and schema profiling for local CSV or JSON tabular datasets without blowing LLM context limits.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to local CSV or JSON tabular file.",
            },
            "sample_rows": {
                "type": "integer",
                "description": "Number of preview rows to inspect (default: 5).",
            },
        },
        "required": ["file_path"],
    },
    return_description="Column types, row counts, null statistics, and sample records.",
    guardian_level=0,
)
async def dataset_summary(file_path: str, sample_rows: int = 5) -> dict[str, Any]:
    p = Path(file_path).resolve()
    if not p.exists() or not p.is_file():
        return {"status": "error", "error": f"File does not exist: {file_path}"}

    ext = p.suffix.lower()
    try:
        rows = []
        if ext == ".csv":
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                total_rows = 0
                null_counts = {h: 0 for h in headers}

                for r in reader:
                    total_rows += 1
                    if total_rows <= sample_rows:
                        rows.append(r)
                    for h in headers:
                        if not r.get(h) or r[h].strip() == "":
                            null_counts[h] += 1
        elif ext == ".json":
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                headers = list(data[0].keys())
                total_rows = len(data)
                null_counts = {h: sum(1 for r in data if r.get(h) is None) for h in headers}
                rows = data[:sample_rows]
            else:
                return {"status": "error", "error": "JSON is not a tabular array of records."}
        else:
            return {"status": "error", "error": f"Unsupported dataset extension '{ext}'. Use .csv or .json."}

        return {
            "status": "success",
            "file": str(p),
            "total_rows": total_rows,
            "columns_count": len(headers),
            "columns": headers,
            "null_counts": null_counts,
            "sample_preview": rows,
        }
    except Exception as e:
        logger.error(f"dataset_summary error: {e}")
        return {"status": "error", "error": str(e)}
