import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.ai.tools.registry import tool_registry
from app.core.logger import logger

# Modern browser fingerprint headers that mirror authentic client sessions
STEALTH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def _clean_extracted_text(text: str) -> str:
    """Normalize whitespace and strip excessive blank lines."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _adaptive_content_extract(soup: BeautifulSoup, target_hint: str | None = None) -> str:
    """
    Self-healing element extraction.
    If target_hint is given, attempts direct lookup, then falls back to semantic
    container matching, and finally main-body text density.
    """
    # Remove script, style, nav, and iframe tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    # Strategy 1: Target hint match (class, id, or tag name)
    if target_hint:
        hint_lower = target_hint.lower()
        # By ID
        found = soup.find(id=re.compile(hint_lower, re.I))
        if found:
            return _clean_extracted_text(found.get_text(separator="\n"))

        # By class
        found = soup.find(class_=re.compile(hint_lower, re.I))
        if found:
            return _clean_extracted_text(found.get_text(separator="\n"))

        # By tag
        found = soup.find(hint_lower)
        if found:
            return _clean_extracted_text(found.get_text(separator="\n"))

    # Strategy 2: Semantic main content tag
    for tag_name in ["article", "main", '[role="main"]', ".content", "#content", ".post"]:
        element = soup.select_one(tag_name)
        if element:
            text = element.get_text(separator="\n")
            if len(text.strip()) > 150:
                return _clean_extracted_text(text)

    # Strategy 3: Text density fallback over body
    body = soup.find("body") or soup
    return _clean_extracted_text(body.get_text(separator="\n"))


@tool_registry.tool(
    name="scrapling_scrape",
    description="Stealth, anti-bot resilient web scraper that emulates modern browser fingerprints and uses self-healing adaptive content extraction.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The target website URL to scrape.",
            },
            "selector_hint": {
                "type": "string",
                "description": "Optional CSS selector, tag, class, or id hint for target data (self-heals if not found).",
            },
            "extract_links": {
                "type": "boolean",
                "description": "Whether to extract key outbound links from the page (default: true).",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum character length of returned text content (default: 8000).",
            },
        },
        "required": ["url"],
    },
    return_description="Extracted title, metadata, sanitized content, and key links.",
    guardian_level=0,
)
async def scrapling_scrape(
    url: str,
    selector_hint: str | None = None,
    extract_links: bool = True,
    max_length: int = 8000,
) -> dict[str, Any]:
    # Basic URL validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return {"status": "error", "error": f"Invalid URL format: {url}"}

    try:
        async with httpx.AsyncClient(
            headers=STEALTH_HEADERS,
            follow_redirects=True,
            timeout=15.0,
        ) as client:
            response = await client.get(url)

        if response.status_code >= 400:
            return {
                "status": "error",
                "status_code": response.status_code,
                "error": f"HTTP {response.status_code} while fetching {url}",
            }

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title and meta description
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        meta_desc = None
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        # Adaptive content extraction
        extracted_text = _adaptive_content_extract(soup, target_hint=selector_hint)
        truncated = False
        if len(extracted_text) > max_length:
            extracted_text = extracted_text[:max_length] + "\n... [content truncated]"
            truncated = True

        links = []
        if extract_links:
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                link_text = a.get_text(strip=True)
                if href.startswith("http") and link_text and len(links) < 20:
                    links.append({"text": link_text[:50], "url": href})

        return {
            "status": "success",
            "url": str(response.url),
            "status_code": response.status_code,
            "title": title,
            "description": meta_desc,
            "content": extracted_text,
            "content_length": len(extracted_text),
            "truncated": truncated,
            "links": links,
        }
    except Exception as e:
        logger.error(f"scrapling_scrape error for {url}: {e}")
        return {"status": "error", "error": str(e)}
