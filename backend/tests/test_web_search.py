from unittest.mock import MagicMock, patch

import pytest

from app.ai.agents.web_search_agent import WebSearchAgent
from app.ai.orchestration.agent_router import route_message
from app.ai.tools.builtin.web_tools import web_fetch, web_search
from app.core.config import settings
from app.core.constants import AgentType


@pytest.mark.asyncio
async def test_web_search_pii_sanitization():
    """Verify data firewall strips user PII and secrets before external query execution."""
    raw_query = "Search for user akash@example.com with key sk-ant-1234567890123456789012"
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"title": "Result 1", "content": "Clean snippet", "url": "https://example.com/1", "engine": "searxng"}
            ]
        }
        mock_get.return_value = mock_resp

        result = await web_search(raw_query)
        assert result["status"] == "success"
        # Verify call params sent to SearXNG did NOT include raw email or API key
        called_kwargs = mock_get.call_args[1]
        sent_query = called_kwargs.get("params", {}).get("q", "")
        assert "akash@example.com" not in sent_query
        assert "1234567890123456789012" not in sent_query
        assert "•••EMAIL_REDACTED•••" in sent_query or "REDACTED" in sent_query


@pytest.mark.asyncio
async def test_web_search_searxng_success():
    """Verify web_search parses SearXNG JSON response properly."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {
                    "title": "FastAPI Release Notes",
                    "content": "FastAPI latest updates and features",
                    "url": "https://fastapi.tiangolo.com/release-notes/",
                    "engine": "searxng",
                },
                {
                    "title": "Python 3.13 Overview",
                    "content": "What's new in Python 3.13",
                    "url": "https://docs.python.org/3.13/",
                    "engine": "searxng",
                },
            ]
        }
        mock_get.return_value = mock_resp

        res = await web_search("FastAPI Python", num_results=2)
        assert res["status"] == "success"
        assert res["provider"] == "searxng"
        assert len(res["results"]) == 2
        assert res["results"][0]["url"] == "https://fastapi.tiangolo.com/release-notes/"


@pytest.mark.asyncio
async def test_web_search_opt_in_disabled():
    """Verify web_search returns disabled status when user setting is off."""
    orig = getattr(settings, "WEB_SEARCH_ENABLED", True)
    try:
        settings.WEB_SEARCH_ENABLED = False
        res = await web_search("quantum computing")
        assert res["status"] == "disabled"
        assert "disabled in Settings" in res["message"]
    finally:
        settings.WEB_SEARCH_ENABLED = orig


@pytest.mark.asyncio
async def test_web_fetch_clean_text_extraction():
    """Verify web_fetch extracts clean text and strips boilerplate."""
    mock_html = """
    <html>
      <head><title>Test Page</title><script>console.log('secret script');</script></head>
      <body>
        <header><nav>Home | About | Contact</nav></header>
        <main>
          <h1>COPPER Offline-First System</h1>
          <p>COPPER operates as a local cognitive operating system designed for privacy and resilience.</p>
        </main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_html
        mock_get.return_value = mock_resp

        res = await web_fetch("https://example.com/copper-docs")
        assert res["status"] == "success"
        assert "COPPER operates as a local cognitive operating system" in res["text"]
        assert "console.log" not in res["text"]


@pytest.mark.asyncio
async def test_web_fetch_invalid_url():
    """Verify web_fetch rejects non-http protocols."""
    res = await web_fetch("file:///C:/passwords.txt")
    assert res["status"] == "error"
    assert "Invalid URL protocol" in res["message"]


@pytest.mark.asyncio
async def test_raptor_react_search_and_synthesis():
    """Verify RAPTOR agent parses <search> tag, feeds observation, and outputs final response with citation."""
    agent = WebSearchAgent()

    # Step 1: Model emits <search>
    llm_step1 = '<search>{"query": "latest rust updates", "num_results": 2}</search>'
    # Step 2: Model emits final synthesis with citation
    llm_step2 = (
        "Rust 1.85 has been released with new edition features and async improvements. "
        "[Source: https://blog.rust-lang.org/2026/02/rust-1.85.0.html]"
    )

    with patch("app.ai.llm.ollama_client.ollama_client.chat", side_effect=[llm_step1, llm_step2]):
        with patch("app.ai.agents.web_search_agent.web_search") as mock_search:
            mock_search.return_value = {
                "status": "success",
                "provider": "searxng",
                "results": [
                    {
                        "title": "Rust 1.85.0 Release",
                        "snippet": "Rust 1.85 features async improvements",
                        "url": "https://blog.rust-lang.org/2026/02/rust-1.85.0.html",
                    }
                ],
            }

            final_answer = await agent.run("What is the latest Rust release?")
            assert "Rust 1.85" in final_answer
            assert "[Source: https://blog.rust-lang.org/2026/02/rust-1.85.0.html]" in final_answer
            mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_raptor_max_three_fetches_limit():
    """Verify RAPTOR agent strictly enforces the maximum 3 page fetches per query turn."""
    agent = WebSearchAgent()

    llm_turns = [
        '<fetch>{"url": "https://example.com/page1"}</fetch>',
        '<fetch>{"url": "https://example.com/page2"}</fetch>',
        '<fetch>{"url": "https://example.com/page3"}</fetch>',
        '<fetch>{"url": "https://example.com/page4"}</fetch>',  # Exceeds max 3
        "Synthesized final response from all three pages. [Source: https://example.com/page1]",
    ]

    with patch("app.ai.llm.ollama_client.ollama_client.chat", side_effect=llm_turns):
        with patch("app.ai.agents.web_search_agent.web_fetch") as mock_fetch:
            mock_fetch.return_value = {"status": "success", "text": "Sample text", "length": 11}

            final_resp = await agent.run("Fetch and compare four articles")
            # web_fetch should have been executed exactly 3 times
            assert mock_fetch.call_count == 3
            assert "Synthesized final response" in final_resp


@pytest.mark.asyncio
async def test_agent_router_web_search_routing():
    """Verify positive keywords route to AgentType.WEB_SEARCH."""
    queries = [
        "search for the latest release of node.js",
        "look up current news about space telescope",
        "what's the latest breaking news today",
        "google current stock price of Apple",
        "find online tutorials for rust async",
        "search the web for artificial intelligence breakthroughs",
    ]
    for q in queries:
        route = await route_message(q)
        assert route == AgentType.WEB_SEARCH, f"Expected '{q}' to route to WEB_SEARCH, got {route}"


@pytest.mark.asyncio
async def test_agent_router_negative_suppression():
    """Verify negative keywords prevent routing to WEB_SEARCH when answering from local knowledge."""
    # Local facts or personal identity -> CHAT
    res_identity = await route_message("who am i and what is my name")
    assert res_identity != AgentType.WEB_SEARCH

    res_notes = await route_message("search in my notes for my password")
    assert res_notes != AgentType.WEB_SEARCH

    # Reminders with search words -> REMINDER
    res_reminder = await route_message("remind me tomorrow to search for groceries")
    assert res_reminder == AgentType.REMINDER

    # Coding requests with search words -> CODING
    res_code = await route_message("write a python function to search for an item in a list")
    assert res_code == AgentType.CODING
