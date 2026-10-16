from app.core.agent_registry import (
    CORE_ACTIVE_AGENTS,
    ROADMAP_PLANNED_AGENTS,
    get_active_agent_count,
    get_model_pool_count,
    get_planned_agent_count,
)
from app.core.constants import AgentType


def test_active_agents_parity_with_agent_type_enum():
    """Asserts that CORE_ACTIVE_AGENTS exactly matches every member of AgentType enum."""
    enum_members = {a.value for a in AgentType}
    registered_ids = {a.id for a in CORE_ACTIVE_AGENTS}

    assert enum_members == registered_ids, (
        f"Drift detected between AgentType enum and CORE_ACTIVE_AGENTS.\n"
        f"Missing in registry: {enum_members - registered_ids}\n"
        f"Extra in registry: {registered_ids - enum_members}"
    )
    assert get_active_agent_count() == 12, "Claim count test failed: Expected exactly 12 core active agents."

def test_model_pools_count():
    """
    Asserts that ModelPoolTier defines exactly 8 functional model pools as documented.
    """
    assert get_model_pool_count() == 8, "Claim count test failed: Expected exactly 8 functional model pools."

def test_planned_roadmap_agents_count():
    """
    Asserts that roadmap planned agents are cataloged and distinct from active agents.
    """
    assert get_planned_agent_count() == 5, "Expected 5 planned roadmap agents."
    active_ids = {a.id for a in CORE_ACTIVE_AGENTS}
    planned_ids = {a.id for a in ROADMAP_PLANNED_AGENTS}
    assert active_ids.isdisjoint(planned_ids), "Active and planned agent IDs must not collide."
