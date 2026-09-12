from typing import Any
from app.ai.tools.registry import tool_registry
from app.ai.agents.agency_catalog import get_persona, list_personas


@tool_registry.tool(
    name="agency_persona_lookup",
    description="Browse and retrieve specialist agent personas and domain directives from C.O.P.P.E.R.'s Agency Catalog.",
    parameters={
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "description": "Optional domain filter (e.g., 'engineering', 'security', 'data_and_ai', 'research_and_science').",
            },
            "persona_id": {
                "type": "string",
                "description": "Specific persona identifier to inspect (optional).",
            },
        },
    },
    return_description="List of personas or details of requested specialist persona.",
    guardian_level=0,
)
async def agency_persona_lookup(
    domain: str | None = None,
    persona_id: str | None = None,
) -> dict[str, Any]:
    if persona_id:
        p = get_persona(persona_id)
        if not p:
            return {"status": "error", "error": f"Persona '{persona_id}' not found."}
        return {"status": "success", "persona": p}

    personas = list_personas(domain)
    return {
        "status": "success",
        "domain_filter": domain,
        "total_available": len(personas),
        "personas": personas,
    }
