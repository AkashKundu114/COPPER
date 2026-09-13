from typing import Any
from app.ai.tools.registry import tool_registry
from app.core.logger import logger


def generate_mermaid_flowchart(nodes: list[dict[str, str]], edges: list[dict[str, str]], direction: str = "TD") -> str:
    """Generate Mermaid flowchart syntax."""
    lines = [f"graph {direction}"]

    shape_templates = {
        "rect": '    {id}["{label}"]',
        "rounded": '    {id}("{label}")',
        "diamond": '    {id}{{"{label}"}}',
        "circle": '    {id}(("{label}"))',
        "subroutine": '    {id}[["{label}"]]',
        "database": '    {id}[("{label}")]',
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


def generate_mermaid_sequence(participants: list[str], messages: list[dict[str, str]]) -> str:
    """Generate Mermaid sequence diagram syntax."""
    lines = ["sequenceDiagram", "    autonumber"]
    for p in participants:
        lines.append(f'    participant {p.replace(" ", "_")} as {p}')
    for m in messages:
        sender = m.get("from", "").replace(" ", "_")
        recipient = m.get("to", "").replace(" ", "_")
        text = m.get("text", "")
        arrow = "-->>" if m.get("is_response") else "->>"
        lines.append(f"    {sender}{arrow}{recipient}: {text}")
    return "\n".join(lines)


def generate_mermaid_er(tables: list[dict[str, Any]]) -> str:
    """Generate Mermaid ER / database schema syntax."""
    lines = ["erDiagram"]
    for t in tables:
        tname = t.get("name", "Table").replace(" ", "_")
        lines.append(f"    {tname} {{")
        for col in t.get("columns", []):
            ctype = col.get("type", "string")
            cname = col.get("name", "col")
            key = "PK" if col.get("pk") else ("FK" if col.get("fk") else "")
            lines.append(f"        {ctype} {cname} {key}".strip())
        lines.append("    }")
    return "\n".join(lines)


@tool_registry.tool(
    name="workflow_diagram_render",
    description="Generate editorial diagrams (flowchart, sequence, ER database schema, architecture) using Mermaid and SVG specifications from diagram-design.",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the architecture, workflow, or system diagram.",
            },
            "diagram_type": {
                "type": "string",
                "enum": ["flowchart", "sequence", "er_diagram", "architecture"],
                "description": "Diagram format type (default: 'flowchart').",
            },
            "steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered steps for flowchart / architecture diagrams.",
            },
            "participants": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Participants list for sequence diagrams (e.g. ['User', 'Router', 'Guardian', 'Agent']).",
            },
            "sequence_messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "from": {"type": "string"},
                        "to": {"type": "string"},
                        "text": {"type": "string"},
                        "is_response": {"type": "boolean"},
                    },
                },
                "description": "Interaction messages for sequence diagrams.",
            },
            "tables": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Table definitions with columns for ER / database schema diagrams.",
            },
        },
        "required": ["title"],
    },
    return_description="Mermaid markdown code block ready for UI rendering.",
    guardian_level=0,
)
async def workflow_diagram_render(
    title: str,
    diagram_type: str = "flowchart",
    steps: list[str] | None = None,
    participants: list[str] | None = None,
    sequence_messages: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        if diagram_type == "sequence" and participants and sequence_messages:
            mermaid_code = generate_mermaid_sequence(participants, sequence_messages)
        elif diagram_type == "er_diagram" and tables:
            mermaid_code = generate_mermaid_er(tables)
        else:
            # Flowchart / Architecture fallback
            step_list = steps or ["Start", "Process Task", "Complete"]
            nodes = [{"id": "START", "label": f"Trigger: {title}", "shape": "circle"}]
            edges = []
            prev_id = "START"

            for i, step in enumerate(step_list, start=1):
                curr_id = f"STEP_{i}"
                shape = "diamond" if any(w in step.lower() for w in ["check", "if", "eval", "verify"]) else "rect"
                nodes.append({"id": curr_id, "label": step, "shape": shape})
                edges.append({"from": prev_id, "to": curr_id})
                prev_id = curr_id

            nodes.append({"id": "END", "label": "Completed", "shape": "circle"})
            edges.append({"from": prev_id, "to": "END"})
            mermaid_code = generate_mermaid_flowchart(nodes, edges)

        return {
            "status": "success",
            "title": title,
            "type": diagram_type,
            "mermaid": f"```mermaid\n{mermaid_code}\n```",
            "raw_code": mermaid_code,
        }
    except Exception as e:
        logger.error(f"workflow_diagram_render error: {e}")
        return {"status": "error", "error": str(e)}
