import re
import urllib.parse
from typing import Any

import httpx

from app.ai.tools.registry import tool_registry
from app.core.config import settings
from app.core.logger import logger


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
    guardian_level=1,  # SUGGEST
)
async def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    # 1. Try local SearXNG if available
    searxng_url = getattr(settings, "SEARXNG_URL", "http://localhost:8080")
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(
                f"{searxng_url}/search",
                params={"q": query, "format": "json"},
            )
            if res.status_code == 200:
                data = res.json()
                raw_results = data.get("results", [])
                results = []
                for r in raw_results[:num_results]:
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("content", ""),
                        "url": r.get("url", ""),
                        "engine": r.get("engine", "searxng"),
                    })
                if results:
                    return {
                        "status": "success",
                        "provider": "searxng",
                        "query": query,
                        "count": len(results),
                        "results": results,
                    }
    except Exception as e:
        logger.debug(f"SearXNG search unavailable, falling back to DuckDuckGo: {e}")

    # 2. DuckDuckGo HTML/Lite Fallback
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        async with httpx.AsyncClient(timeout=8.0, headers=headers, follow_redirects=True) as client:
            res = await client.get(url)
            if res.status_code == 200:
                html = res.text
                results = []
                # Simple regex parsing for DuckDuckGo HTML results
                # Look for result__body / result__snippet
                matches = re.findall(
                    r'<a class="result__url" href="([^"]+)".*?<a class="result__snippet[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL,
                )
                if not matches:
                    # Alternative regex
                    title_matches = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
                    snippet_matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)
                    for idx in range(min(len(title_matches), len(snippet_matches), num_results)):
                        clean_title = re.sub(r"<[^>]+>", "", title_matches[idx][1]).strip()
                        clean_snippet = re.sub(r"<[^>]+>", "", snippet_matches[idx]).strip()
                        raw_link = title_matches[idx][0]
                        # DuckDuckGo redirect unwrapper
                        if "uddg=" in raw_link:
                            unwrapped = urllib.parse.unquote(raw_link.split("uddg=")[-1].split("&")[0])
                        else:
                            unwrapped = raw_link
                        results.append({
                            "title": clean_title,
                            "snippet": clean_snippet,
                            "url": unwrapped,
                            "engine": "duckduckgo",
                        })
                else:
                    for link, snippet in matches[:num_results]:
                        clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                        results.append({
                            "title": query,
                            "snippet": clean_snippet,
                            "url": link.strip(),
                            "engine": "duckduckgo",
                        })

                if results:
                    return {
                        "status": "success",
                        "provider": "duckduckgo",
                        "query": query,
                        "count": len(results),
                        "results": results,
                    }
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")

    return {
        "status": "partial",
        "provider": "offline_notice",
        "query": query,
        "count": 0,
        "results": [],
        "message": f"Web search could not retrieve live results for '{query}'. Local offline reasoning is active.",
    }
