from typing import Any
from app.ai.tools.registry import tool_registry
from app.core.logger import logger


def generate_mermaid_flowchart(nodes: list[dict[str, str]], edges: list[dict[str, str]], direction: str = "TD") -> str:
    """
    Generate Mermaid markdown diagram syntax from nodes and directed edges.
    nodes format: [{"id": "A", "label": "Start", "shape": "circle|rect|diamond"}]
    edges format: [{"from": "A", "to": "B", "label": "optional text"}]
    """
    lines = [f"graph {direction}"]

    shape_templates = {
        "rect": '    {id}["{label}"]',
        "rounded": '    {id}("{label}")',
        "diamond": '    {id}{{"{label}"}}',
        "circle": '    {id}(("{label}"))',
        "subroutine": '    {id}[["{label}"]]',
    }

    for node in nodes:
        nid = node.get("id", "node")
        label = node.get("label", nid).replace('"', "'")
        shape = node.get("shape", "rect")
        template = shape_templates.get(shape, shape_templates["rect"])
        lines.append(template.format(id=nid, label=label))

    for edge in edges:
        u = edge.get("from")
        v = edge.get("to")
        elabel = edge.get("label")
        if elabel:
            lines.append(f'    {u} -->|"{elabel}"| {v}')
        else:
            lines.append(f"    {u} --> {v}")

    return "\n".join(lines)


@tool_registry.tool(
    name="workflow_diagram_render",
    description="Generate clean Mermaid flowchart code to visualize multi-agent handoffs, execution DAGs, or system architectures.",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the architecture or workflow diagram.",
            },
            "steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Sequential steps or agent actions to visualize.",
            },
            "branching": {
                "type": "boolean",
                "description": "Whether to visualize decision points or parallel steps (default: false).",
            },
        },
        "required": ["title", "steps"],
    },
    return_description="Mermaid markdown code block ready for UI rendering.",
    guardian_level=0,
)
async def workflow_diagram_render(
    title: str,
    steps: list[str],
    branching: bool = False,
) -> dict[str, Any]:
    try:
        nodes = []
        edges = []

        # Start node
        nodes.append({"id": "START", "label": f"Trigger: {title}", "shape": "circle"})

        prev_id = "START"
        for i, step in enumerate(steps, start=1):
            curr_id = f"STEP_{i}"
            shape = "diamond" if (branching and ("check" in step.lower() or "if" in step.lower())) else "rect"
            nodes.append({"id": curr_id, "label": step, "shape": shape})
            edges.append({"from": prev_id, "to": curr_id})
            prev_id = curr_id

        # End node
        nodes.append({"id": "END", "label": "Completed", "shape": "circle"})
        edges.append({"from": prev_id, "to": "END"})

        mermaid_code = generate_mermaid_flowchart(nodes, edges)

        return {
            "status": "success",
            "title": title,
            "mermaid": f"```mermaid\n{mermaid_code}\n```",
            "raw_code": mermaid_code,
        }
    except Exception as e:
        logger.error(f"workflow_diagram_render error: {e}")
        return {"status": "error", "error": str(e)}
