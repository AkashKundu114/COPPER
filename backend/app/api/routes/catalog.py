from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.ai.agents.agency_catalog import _load_catalog, get_persona
from app.ai.tools.builtin.diagram_tools import workflow_diagram_render
from app.ai.tools.builtin.science_catalog_tools import _load_science_skills
from app.ai.tools.builtin.science_tools import arxiv_search
from app.ai.tools.builtin.video_tools import video_pipeline_list
from app.ai.tools.registry import tool_registry

router = APIRouter(prefix="/catalog", tags=["catalog"])


class DiagramRenderRequest(BaseModel):
    diagram_type: str = "flowchart"
    title: str = "System Workflow"
    specification: str = ""


@router.get("/summary")
async def get_catalog_summary():
    """Get high-level counts and distribution across all 8 integrated repositories."""
    agency_data = _load_catalog()
    science_data = _load_science_skills()
    tools = tool_registry.list_tools()

    # Division counts
    division_counts: dict[str, int] = {}
    for p in agency_data.values():
        div = p.get("division", "other")
        division_counts[div] = division_counts.get(div, 0) + 1

    # Science category counts
    science_categories: dict[str, int] = {}
    for s in science_data.values():
        cat = s.get("category", "General")
        science_categories[cat] = science_categories.get(cat, 0) + 1

    # Tool guardian level counts
    guardian_counts: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0}
    for t in tools:
        lvl = getattr(t, "guardian_level", 0)
        guardian_counts[lvl] = guardian_counts.get(lvl, 0) + 1

    return {
        "total_personas": len(agency_data),
        "total_divisions": len(division_counts),
        "total_scientific_skills": len(science_data),
        "total_tools": len(tools),
        "divisions": [{"id": k, "count": v} for k, v in sorted(division_counts.items(), key=lambda x: -x[1])],
        "science_categories": [
            {"name": k, "count": v} for k, v in sorted(science_categories.items(), key=lambda x: -x[1])
        ],
        "guardian_tiers": guardian_counts,
    }


@router.get("/divisions")
async def get_divisions():
    """List all divisions in the 264 Agency Personas catalog."""
    catalog = _load_catalog()
    divisions_map: dict[str, dict[str, Any]] = {}

    for k, p in catalog.items():
        div = p.get("division", "other")
        div_label = p.get("division_label", div.capitalize())
        if div not in divisions_map:
            divisions_map[div] = {
                "id": div,
                "label": div_label,
                "count": 0,
                "sample_roles": [],
            }
        divisions_map[div]["count"] += 1
        if len(divisions_map[div]["sample_roles"]) < 3:
            divisions_map[div]["sample_roles"].append(p.get("name", k))

    return list(divisions_map.values())


@router.get("/personas")
async def get_personas(
    division: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=300),
    offset: int = Query(0, ge=0),
):
    """List agency personas with division and keyword filtering."""
    catalog = _load_catalog()
    filtered = []
    search_term = search.lower().strip() if search else None
    div_filter = division.lower().strip() if division and division != "all" else None

    for key, p in catalog.items():
        if div_filter and p.get("division", "").lower() != div_filter:
            continue

        if search_term:
            name = p.get("name", "").lower()
            role = p.get("role", "").lower()
            desc = p.get("description", "").lower()
            vibe = p.get("vibe", "").lower()
            if (
                search_term not in name
                and search_term not in role
                and search_term not in desc
                and search_term not in vibe
                and search_term not in key.lower()
            ):
                continue

        filtered.append(
            {
                "id": key,
                "name": p.get("name", key),
                "division": p.get("division", "general"),
                "division_label": p.get("division_label", ""),
                "role": p.get("role", p.get("name", "")),
                "description": p.get("description", ""),
                "vibe": p.get("vibe", "Professional, autonomous, focused"),
                "system_prompt_preview": (p.get("system_prompt", "")[:180] + "...") if p.get("system_prompt") else "",
            }
        )

    total = len(filtered)
    paginated = filtered[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "personas": paginated,
    }


@router.get("/personas/{persona_id:path}")
async def get_persona_detail(persona_id: str):
    """Get full details and system directive for a single specialist persona."""
    persona = get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found.")
    return persona


@router.get("/scientific-skills")
async def get_scientific_skills(
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List 165+ scientific skills with category and search filtering."""
    skills = _load_science_skills()
    filtered = []
    search_term = search.lower().strip() if search else None
    cat_filter = category.lower().strip() if category and category != "all" else None

    for key, s in skills.items():
        if cat_filter and s.get("category", "").lower() != cat_filter:
            continue

        if search_term:
            name = s.get("name", "").lower()
            desc = s.get("description", "").lower()
            path = s.get("path", "").lower()
            if (
                search_term not in name
                and search_term not in desc
                and search_term not in key.lower()
                and search_term not in path
            ):
                continue

        filtered.append(
            {
                "id": key,
                "name": s.get("name", key),
                "category": s.get("category", "General"),
                "description": s.get("description", ""),
                "path": s.get("path", ""),
                "instruction_preview": (s.get("instructions", "")[:160] + "...") if s.get("instructions") else "",
            }
        )

    total = len(filtered)
    paginated = filtered[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "skills": paginated,
    }


@router.get("/scientific-skills/{skill_id}")
async def get_scientific_skill_detail(skill_id: str):
    """Get complete guidelines and prompt instructions for a scientific skill."""
    skills = _load_science_skills()
    skill_key = skill_id.lower().strip()
    if skill_key in skills:
        return skills[skill_key]

    # Partial match fallback
    for k, v in skills.items():
        if skill_key in k.lower() or skill_key in v.get("name", "").lower():
            return v

    raise HTTPException(status_code=404, detail=f"Scientific skill '{skill_id}' not found.")


@router.get("/tools")
async def get_tools_catalog(
    search: str | None = None,
    guardian_level: int | None = None,
):
    """List all registered tools in C.O.P.P.E.R. with guardian safety metadata."""
    tools = tool_registry.list_tools()
    search_term = search.lower().strip() if search else None

    result = []
    for t in tools:
        if guardian_level is not None and getattr(t, "guardian_level", 0) != guardian_level:
            continue

        if search_term:
            name = t.name.lower()
            desc = t.description.lower()
            ret_desc = getattr(t, "return_description", "").lower()
            if search_term not in name and search_term not in desc and search_term not in ret_desc:
                continue

        props = t.parameters.get("properties", {})
        required = t.parameters.get("required", [])
        param_list = [
            {
                "name": p_name,
                "type": p_data.get("type", "any"),
                "description": p_data.get("description", ""),
                "required": p_name in required,
            }
            for p_name, p_data in props.items()
        ]

        result.append(
            {
                "name": t.name,
                "description": t.description,
                "return_description": getattr(t, "return_description", "Tool execution result"),
                "guardian_level": getattr(t, "guardian_level", 0),
                "parameters": param_list,
                "parameter_count": len(param_list),
                "category": _infer_tool_category(t.name),
            }
        )

    # Sort tools by category, then by name
    result.sort(key=lambda x: (x["category"], x["name"]))

    return {
        "total": len(result),
        "tools": result,
    }


def _infer_tool_category(tool_name: str) -> str:
    n = tool_name.lower()
    if any(k in n for k in ["codebase", "git", "diff", "symbol"]):
        return "Codebase & VCS"
    if any(k in n for k in ["scrapling", "scrape", "search", "web", "fetch"]):
        return "Web & Stealth Scraping"
    if any(k in n for k in ["science", "arxiv", "dataset", "scientific"]):
        return "Science & Research"
    if any(k in n for k in ["diagram", "render", "flowchart"]):
        return "Visuals & Architecture"
    if any(k in n for k in ["video", "openmontage", "slideshow"]):
        return "Video & Multimedia"
    if any(k in n for k in ["system", "hardware", "process", "screen", "clipboard"]):
        return "System & Hardware"
    if any(k in n for k in ["memory", "profile", "cognitive", "causal"]):
        return "Memory & Cognition"
    return "Operations & Fleet"


@router.post("/diagram/render")
async def render_diagram_api(req: DiagramRenderRequest):
    """Execute workflow diagram rendering."""
    return await workflow_diagram_render(
        diagram_type=req.diagram_type,
        title=req.title,
        specification=req.specification,
    )


@router.get("/video/pipelines")
async def get_video_pipelines():
    """Retrieve available OpenMontage video pipelines and presets."""
    return await video_pipeline_list()


class ArxivSearchRequest(BaseModel):
    query: str
    max_results: int = 5


@router.post("/arxiv/search")
async def search_arxiv_api(req: ArxivSearchRequest):
    """Search arXiv preprints directly using science tools."""
    return await arxiv_search(query=req.query, max_results=req.max_results)
