import json
from pathlib import Path
from typing import Any
from app.core.logger import logger

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "agency_agents_full_catalog.json"
_CACHED_CATALOG: dict[str, dict[str, Any]] | None = None


def _load_catalog() -> dict[str, dict[str, Any]]:
    global _CACHED_CATALOG
    if _CACHED_CATALOG is not None:
        return _CACHED_CATALOG

    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                _CACHED_CATALOG = json.load(f)
                return _CACHED_CATALOG
        except Exception as e:
            logger.error(f"Failed to load full agency catalog from {CATALOG_PATH}: {e}")

    _CACHED_CATALOG = {}
    return _CACHED_CATALOG


def get_persona(identifier: str) -> dict[str, Any] | None:
    """
    Retrieve persona definition by key identifier.
    Supports either 'division:agent-id' (e.g. 'engineering:engineering-software-architect')
    or partial matching by role name / slug (e.g. 'devops_engineer', 'software_architect').
    """
    catalog = _load_catalog()
    if identifier in catalog:
        return catalog[identifier]

    id_lower = identifier.lower().replace("_", "-")
    # Search by exact key match or slug match
    for key, p in catalog.items():
        slug = key.split(":")[-1].lower()
        if slug == id_lower or id_lower in slug or identifier.lower() == p.get("name", "").lower():
            return p

    return None


def list_personas(division: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List available specialist personas, optionally filtered by division."""
    catalog = _load_catalog()
    res = []
    div_filter = division.lower() if division else None

    for key, val in catalog.items():
        if div_filter is None or val.get("division", "").lower() == div_filter:
            res.append({
                "id": key,
                "name": val.get("name"),
                "division": val.get("division"),
                "division_label": val.get("division_label"),
                "description": val.get("description", ""),
                "vibe": val.get("vibe", ""),
            })
            if len(res) >= limit:
                break
    return res


def list_divisions() -> list[str]:
    """Return all unique agent divisions in C.O.P.P.E.R."""
    catalog = _load_catalog()
    return sorted(list({p.get("division") for p in catalog.values() if p.get("division")}))


def inject_persona(system_prompt: str, persona_id: str) -> str:
    """Inject specialist persona directive into a system prompt."""
    persona = get_persona(persona_id)
    if not persona:
        return system_prompt

    directive = persona.get("system_prompt") or persona.get("description", "")
    return (
        f"{system_prompt}\n\n"
        f"[SPECIALIST PERSONA ACTIVE: {persona.get('name', persona_id)} | Division: {persona.get('division_label', '')}]\n"
        f"{directive}"
    )
