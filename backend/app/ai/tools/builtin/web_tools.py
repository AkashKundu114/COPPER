import html
import re
import urllib.parse
from typing import Any

import httpx

from app.ai.tools.registry import tool_registry
from app.core.config import settings
from app.core.data_firewall import redact
from app.core.logger import logger

try:
    import trafilatura
except ImportError:
    trafilatura = None


def _log_web_audit(
    category: str,
    actor: str,
    summary: str,
    detail: str | None = None,
    session_id: str | None = None,
) -> None:
    """Safely log web access events in COPPER audit trail."""
    try:
        from app.database.models.audit_log import AuditLogEntry
        from app.database.postgres import SessionLocal

        db = SessionLocal()
        try:
            entry = AuditLogEntry(
                session_id=session_id,
                category=category,
                actor=actor,
                summary=redact(summary[:300]),
                detail=redact(detail) if detail else None,
                scope="external",
            )
            db.add(entry)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Audit log entry skipped: {e}")


def _fallback_extract_text(html_content: str, max_chars: int = 6000) -> str:
    """Fallback plain-text extractor when trafilatura is unavailable."""
    # Strip script and style blocks
    cleaned = re.sub(r"<(script|style|nav|header|footer)[^>]*>[\s\S]*?</\1>", " ", html_content, flags=re.IGNORECASE)
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_chars]


@tool_registry.tool(
    name="web_search",
    description="Search the web for up-to-date information, documentation, news, or external sources.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query string."},
            "num_results": {
                "type": "integer",
                "description": "Maximum number of search results to return (default 5).",
            },
        },
        "required": ["query"],
    },
    return_description="List of search result items with title, snippet, and URL.",
    guardian_level=1,  # Level 1: SUGGEST (Logged, opt-in via Settings)
)
async def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    # Check Settings opt-in
    if not getattr(settings, "WEB_SEARCH_ENABLED", True):
        return {
            "status": "disabled",
            "message": "Web search is currently disabled in Settings. Please enable web search in Settings to perform live external searches.",
            "results": [],
        }

    # Data firewall: Strip user PII and secrets before sending query outside
    sanitized_query = redact(query).strip()

    # 1. Try local SearXNG at configured URL (default localhost:8888)
    searxng_url = getattr(settings, "SEARXNG_URL", "http://localhost:8888")
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(
                f"{searxng_url}/search",
                params={"q": sanitized_query, "format": "json"},
            )
            if res.status_code == 200:
                data = res.json()
                raw_results = data.get("results", [])
                results = []
                for r in raw_results[:num_results]:
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "snippet": r.get("content", ""),
                            "url": r.get("url", ""),
                            "engine": r.get("engine", "searxng"),
                        }
                    )
                if results:
                    _log_web_audit(
                        category="external_api_accessed",
                        actor="raptor_web_search",
                        summary=f"SearXNG query: {sanitized_query}",
                        detail=f"Retrieved {len(results)} results from {searxng_url}",
                    )
                    return {
                        "status": "success",
                        "provider": "searxng",
                        "query": sanitized_query,
                        "count": len(results),
                        "results": results,
                    }
    except Exception as e:
        logger.debug(f"SearXNG search unavailable at {searxng_url}, falling back to DuckDuckGo: {e}")

    # 2. DuckDuckGo HTML Fallback
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        encoded_query = urllib.parse.quote_plus(sanitized_query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True) as client:
            res = await client.get(url)
            if res.status_code == 200:
                html_text = res.text
                results = []
                matches = re.findall(
                    r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>',
                    html_text,
                    re.DOTALL,
                )
                if not matches:
                    title_matches = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text)
                    snippet_matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html_text)
                    for idx in range(min(len(title_matches), len(snippet_matches), num_results)):
                        clean_title = re.sub(r"<[^>]+>", "", title_matches[idx][1]).strip()
                        clean_snippet = re.sub(r"<[^>]+>", "", snippet_matches[idx]).strip()
                        raw_link = title_matches[idx][0]
                        if "uddg=" in raw_link:
                            unwrapped = urllib.parse.unquote(raw_link.split("uddg=")[-1].split("&")[0])
                        else:
                            unwrapped = raw_link
                        results.append(
                            {
                                "title": clean_title,
                                "snippet": clean_snippet,
                                "url": unwrapped,
                                "engine": "duckduckgo",
                            }
                        )
                else:
                    for link, snippet in matches[:num_results]:
                        clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                        results.append(
                            {
                                "title": sanitized_query,
                                "snippet": clean_snippet,
                                "url": link.strip(),
                                "engine": "duckduckgo",
                            }
                        )

                if results:
                    _log_web_audit(
                        category="external_api_accessed",
                        actor="raptor_web_search",
                        summary=f"DuckDuckGo fallback query: {sanitized_query}",
                        detail=f"Retrieved {len(results)} results via DuckDuckGo fallback",
                    )
                    return {
                        "status": "success",
                        "provider": "duckduckgo",
                        "query": sanitized_query,
                        "count": len(results),
                        "results": results,
                    }
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")

    _log_web_audit(
        category="external_api_accessed",
        actor="raptor_web_search",
        summary=f"Web search attempt yielded no results: {sanitized_query}",
    )
    return {
        "status": "partial",
        "provider": "offline_notice",
        "query": sanitized_query,
        "count": 0,
        "results": [],
        "message": f"Web search could not retrieve live results for '{sanitized_query}'. Local offline reasoning is active.",
    }


@tool_registry.tool(
    name="web_fetch",
    description="Fetch a web page by URL and extract its clean text content using trafilatura.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL of the webpage to fetch."},
            "extract": {
                "type": "string",
                "description": "Extraction mode ('text'). Default is 'text'.",
                "default": "text",
            },
        },
        "required": ["url"],
    },
    return_description="Extracted clean text content of the webpage.",
    guardian_level=1,  # Level 1: SUGGEST
)
async def web_fetch(url: str, extract: str = "text") -> dict[str, Any]:
    # Check Settings opt-in
    if not getattr(settings, "WEB_SEARCH_ENABLED", True):
        return {
            "status": "disabled",
            "message": "Web access is currently disabled in Settings.",
            "url": url,
            "text": "",
        }

    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        return {
            "status": "error",
            "message": "Invalid URL protocol. URL must start with http:// or https://",
            "url": clean_url,
            "text": "",
        }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
            res = await client.get(clean_url)
            if res.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to fetch page. HTTP status code: {res.status_code}",
                    "url": clean_url,
                    "text": "",
                }

            html_content = res.text

            # Extract clean text using trafilatura if available
            extracted_text = ""
            if trafilatura is not None:
                try:
                    extracted_text = trafilatura.extract(
                        html_content,
                        include_links=False,
                        include_images=False,
                        favor_precision=True,
                    ) or ""
                except Exception as ex:
                    logger.debug(f"trafilatura extraction error on {clean_url}: {ex}")

            if not extracted_text:
                extracted_text = _fallback_extract_text(html_content, max_chars=6000)

            # Cap length to 6000 characters for token context budget
            extracted_text = extracted_text[:6000].strip()

            _log_web_audit(
                category="external_api_accessed",
                actor="raptor_web_fetch",
                summary=f"Web fetch URL: {clean_url}",
                detail=f"Extracted {len(extracted_text)} characters using {'trafilatura' if trafilatura else 'fallback'}",
            )

            return {
                "status": "success",
                "url": clean_url,
                "text": extracted_text,
                "length": len(extracted_text),
                "extractor": "trafilatura" if trafilatura else "fallback_html",
            }
    except Exception as e:
        logger.warning(f"Error fetching URL {clean_url}: {e}")
        return {
            "status": "error",
            "message": f"Error fetching web page: {str(e)}",
            "url": clean_url,
            "text": "",
        }
