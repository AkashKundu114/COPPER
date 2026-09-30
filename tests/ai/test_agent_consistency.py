import os
import re
import pytest
from pathlib import Path

from app.core.constants import AgentType
from app.services.chat_service import AGENT_MAP
from app.ai.orchestration.agent_router import KEYWORD_RULES, _ROUTING_PATTERNS


def parse_frontend_active_agents() -> list[dict[str, str]]:
    """Parse ACTIVE_AGENTS definitions directly from frontend/src/constants/agents.ts."""
    repo_root = Path(__file__).resolve().parents[2]
    agents_ts_path = repo_root / "frontend" / "src" / "constants" / "agents.ts"
    assert agents_ts_path.exists(), f"Frontend agents.ts not found at {agents_ts_path}"

    content = agents_ts_path.read_text(encoding="utf-8")

    # Extract block between 'export const ACTIVE_AGENTS' and 'export const PLANNED_AGENTS'
    match = re.search(
        r"export\s+const\s+ACTIVE_AGENTS:\s*AgentMeta\[\]\s*=\s*\[([\s\S]*?)\];",
        content,
    )
    assert match, "Could not locate ACTIVE_AGENTS array in frontend/src/constants/agents.ts"

    active_block = match.group(1)

    # Extract all agent id fields
    agent_ids = re.findall(r'id:\s*["\']([^"\']+)["\']', active_block)
    agent_names = re.findall(r'name:\s*["\']([^"\']+)["\']', active_block)

    return [{"id": aid, "name": aname} for aid, aname in zip(agent_ids, agent_names)]


def test_agent_type_count_is_twelve():
    """Assert AgentType enum contains exactly 12 fully implemented core agents."""
    expected_agents = {
        "chat",
        "coding",
        "document",
        "automation",
        "reminder",
        "research",
        "vision",
        "image",
        "web_search",
        "campaign_intelligence",
        "planner",
        "guardian",
    }
    actual_agents = {a.value for a in AgentType}
    assert len(AgentType) == 12, f"Expected 12 AgentType members, found {len(AgentType)}: {actual_agents}"
    assert actual_agents == expected_agents, f"AgentType enum values mismatch: {actual_agents ^ expected_agents}"


def test_backend_matches_frontend_active_agents_count_and_keys():
    """Assert len(AgentType) matches frontend ACTIVE_AGENTS count and IDs exactly."""
    frontend_agents = parse_frontend_active_agents()
    frontend_ids = {a["id"] for a in frontend_agents}
    backend_ids = {a.value for a in AgentType}

    assert len(AgentType) == len(frontend_agents), (
        f"Agent count mismatch: Backend AgentType has {len(AgentType)} agents, "
        f"frontend ACTIVE_AGENTS has {len(frontend_agents)} agents."
    )
    assert backend_ids == frontend_ids, (
        f"Agent ID mismatch between backend and frontend: "
        f"Backend unique: {backend_ids - frontend_ids}, Frontend unique: {frontend_ids - backend_ids}"
    )


def test_every_agent_type_has_registered_handler():
    """
    Verify every agent type in AgentType has a registered handler in AGENT_MAP.
    Fails if someone adds an enum value without a handler.
    """
    missing_handlers = [agent for agent in AgentType if agent not in AGENT_MAP]
    assert not missing_handlers, f"The following AgentType members lack registered handlers in AGENT_MAP: {missing_handlers}"

    assert len(AGENT_MAP) == len(AgentType), (
        f"AGENT_MAP count ({len(AGENT_MAP)}) does not match AgentType count ({len(AgentType)})"
    )

    for agent_type, handler in AGENT_MAP.items():
        assert handler is not None, f"Handler for {agent_type} is None"
        assert hasattr(handler, "run"), f"Handler for {agent_type} missing 'run' coroutine"
        assert callable(getattr(handler, "run")), f"Handler {agent_type}.run is not callable"
        assert hasattr(handler, "name") and bool(handler.name), f"Handler for {agent_type} missing name"
        assert hasattr(handler, "description") and bool(handler.description), (
            f"Handler for {agent_type} missing description"
        )
        assert hasattr(handler, "get_target_model") and bool(handler.get_target_model()), (
            f"Handler for {agent_type} missing get_target_model()"
        )


def test_topology_router_routes_only_to_implemented_agents():
    """Verify that routing table and rules only target implemented AgentType values."""
    for agent_type in KEYWORD_RULES.keys():
        assert isinstance(agent_type, AgentType), f"KEYWORD_RULES contains non-AgentType key: {agent_type}"
        assert agent_type in AGENT_MAP, f"KEYWORD_RULES targets unhandled agent: {agent_type}"

    for pattern, agent_type in _ROUTING_PATTERNS:
        assert isinstance(agent_type, AgentType), f"_ROUTING_PATTERNS routes to non-AgentType: {agent_type}"
        assert agent_type in AGENT_MAP, f"_ROUTING_PATTERNS targets unhandled agent: {agent_type}"


def test_fails_if_unregistered_enum_added():
    """Verify safeguard: If an enum value is not registered in AGENT_MAP, assertion fails."""
    # Test our verification function with simulated unhandled agent
    class MockAgentType:
        CHAT = "chat"
        UNIMPLEMENTED = "unimplemented_rogue_agent"

    unhandled = [k for k in [MockAgentType.CHAT, MockAgentType.UNIMPLEMENTED] if k not in AGENT_MAP]
    assert "unimplemented_rogue_agent" in unhandled, "Safety check should identify unhandled agent"
