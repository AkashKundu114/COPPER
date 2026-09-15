import json
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger

CATALOG_PATH = Path(__file__).resolve().parents[4] / "data" / "scientific_skills_catalog.json"
_SKILLS_CACHE: dict[str, dict[str, Any]] | None = None


def _load_science_skills() -> dict[str, dict[str, Any]]:
    global _SKILLS_CACHE
    if _SKILLS_CACHE is not None:
        return _SKILLS_CACHE

    if CATALOG_PATH.exists():
        try:
            with open(CATALOG_PATH, encoding="utf-8") as f:
                _SKILLS_CACHE = json.load(f)
                return _SKILLS_CACHE
        except Exception as e:
            logger.error(f"Failed to load science skills catalog: {e}")

    _SKILLS_CACHE = {}
    return _SKILLS_CACHE


@tool_registry.tool(
    name="scientific_skill_lookup",
    description="Retrieve domain-expert operational guidelines, formulas, recommended Python libraries, and workflow steps for 165+ scientific agent skills.",
    parameters={
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "The scientific discipline or tool (e.g. 'biopython', 'rdkit', 'sympy', 'scanpy', 'anndata', 'scikit-learn', 'timesfm-forecasting', 'literature-review').",
            }
        },
        "required": ["skill_name"],
    },
    return_description="Detailed guidelines, instructions, and workflows for the scientific domain.",
    guardian_level=0,
)
async def scientific_skill_lookup(skill_name: str) -> dict[str, Any]:
    catalog = _load_science_skills()
    q = skill_name.lower().strip()

    # Exact match
    if q in catalog:
        return {"status": "success", "skill": catalog[q]}

    # Partial match
    matches = []
    for k, v in catalog.items():
        if q in k or q in v.get("name", "").lower() or q in v.get("description", "").lower():
            matches.append({"id": k, "name": v.get("name"), "description": v.get("description", "")[:120]})

    if len(matches) == 1:
        return {"status": "success", "skill": catalog[matches[0]["id"]]}
    elif len(matches) > 1:
        return {
            "status": "multiple_matches",
            "query": skill_name,
            "count": len(matches),
            "suggestions": matches[:10],
        }

    return {
        "status": "error",
        "error": f"No scientific skill matching '{skill_name}' found in catalog.",
    }


@tool_registry.tool(
    name="scientific_skill_list",
    description="List available scientific agent skills across bioinformatics, chemistry, mathematics, physics, and ML.",
    parameters={
        "type": "object",
        "properties": {
            "filter_query": {
                "type": "string",
                "description": "Optional keyword to filter skills (e.g. 'bio', 'chem', 'math', 'ai', 'data').",
            },
            "limit": {
                "type": "integer",
                "description": "Max skills to return (default: 30).",
            },
        },
    },
    return_description="List of available scientific skills with summary descriptions.",
    guardian_level=0,
)
async def scientific_skill_list(filter_query: str | None = None, limit: int = 30) -> dict[str, Any]:
    catalog = _load_science_skills()
    results = []
    fq = filter_query.lower() if filter_query else None

    for k, v in catalog.items():
        if fq is None or fq in k or fq in v.get("name", "").lower() or fq in v.get("description", "").lower():
            results.append(
                {
                    "id": k,
                    "name": v.get("name"),
                    "description": v.get("description", "")[:120],
                }
            )
            if len(results) >= limit:
                break

    return {
        "status": "success",
        "total_available": len(catalog),
        "returned": len(results),
        "skills": results,
    }
