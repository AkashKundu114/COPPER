import re
from typing import Any

from app.ai.knowledge.graph_store import canonicalize_name, graph_store
from app.ai.memory.memory_manager import memory_manager
from app.core.logger import logger


class GraphRAG:
    def __init__(self):
        pass

    def extract_mentioned_entities(self, query: str) -> list[str]:
        """
        Extracts entities present in the knowledge graph that are mentioned in the query.
        Matches case-insensitively with word-boundary awareness.
        """
        if not query or not query.strip():
            return []

        graph_store._ensure_initialized()
        query_text = query.strip()
        matched_canons: list[str] = []

        # Get all node canonical names and display names, sorted by length descending
        candidates = []
        for node_canon, data in graph_store.graph.nodes(data=True):
            display_name = data.get("name", node_canon)
            candidates.append((len(display_name), node_canon, display_name))

        candidates.sort(key=lambda x: x[0], reverse=True)

        for _, canon, display_name in candidates:
            # Word boundary regex search
            pattern = rf"\b{re.escape(display_name)}\b"
            if re.search(pattern, query_text, re.IGNORECASE):
                if canon not in matched_canons:
                    matched_canons.append(canon)
            elif display_name.lower() in query_text.lower() and len(display_name) > 3:
                if canon not in matched_canons:
                    matched_canons.append(canon)

        return matched_canons

    def get_relevant_relationships(
        self, query: str, max_relationships: int = 10, min_confidence: float = 0.5
    ) -> list[dict[str, Any]]:
        """
        Extracts mentioned entities and fetches their ranked graph relationships.
        """
        mentioned_entities = self.extract_mentioned_entities(query)
        if not mentioned_entities:
            return []

        collected_edges: list[dict[str, Any]] = []
        seen_edge_keys = set()

        for canon in mentioned_entities:
            neighborhood = graph_store.query_neighbors(canon, depth=1, min_confidence=min_confidence)
            for edge in neighborhood.get("edges", []):
                # Unique key across directed endpoints and relation type
                edge_key = (
                    canonicalize_name(edge.get("source", "")),
                    canonicalize_name(edge.get("target", "")),
                    edge.get("type", ""),
                )
                if edge_key not in seen_edge_keys:
                    seen_edge_keys.add(edge_key)
                    collected_edges.append(edge)

        # Rank by confidence descending, then evidence count
        collected_edges.sort(
            key=lambda x: (x.get("confidence", 0.0), x.get("evidence_count", 1)),
            reverse=True,
        )

        return collected_edges[:max_relationships]

    def format_graph_context(self, relationships: list[dict[str, Any]]) -> str:
        """
        Formats extracted relationships into the standard ATLAS knowledge graph context block:
        KNOWLEDGE GRAPH CONTEXT:
        - Akash WORKS_ON COPPER (confidence: 95%)
        - COPPER USES FastAPI (confidence: 90%)
        """
        if not relationships:
            return ""

        lines = ["KNOWLEDGE GRAPH CONTEXT:"]
        for rel in relationships:
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            rtype = rel.get("type", "RELATED_TO")
            conf = rel.get("confidence", 0.8)
            conf_pct = int(round(conf * 100))
            lines.append(f"- {src} {rtype} {tgt} (confidence: {conf_pct}%)")

        return "\n".join(lines)

    async def get_graph_context(self, query: str, max_relationships: int = 10, min_confidence: float = 0.5) -> str:
        """
        End-to-end extraction and formatting of graph context for an agent query.
        """
        try:
            rels = self.get_relevant_relationships(
                query, max_relationships=max_relationships, min_confidence=min_confidence
            )
            return self.format_graph_context(rels)
        except Exception as e:
            logger.warning(f"[ATLAS GraphRAG] Error extracting graph context: {e}")
            return ""

    async def search_graph_and_vector(
        self, query: str, session_id: str | None = None, limit: int = 5
    ) -> dict[str, Any]:
        """
        Merges graph neighborhood context with vector memories for holistic retrieval.
        """
        graph_rels = self.get_relevant_relationships(query, max_relationships=limit)
        graph_ctx = self.format_graph_context(graph_rels)

        vector_ctx = ""
        try:
            vector_ctx = await memory_manager.search_relevant_context(query, session_id=session_id, limit=limit)
        except Exception as e:
            logger.warning(f"[ATLAS GraphRAG] Vector search fallback: {e}")

        return {
            "graph_context": graph_ctx,
            "relationships": graph_rels,
            "vector_context": vector_ctx,
        }


graph_rag = GraphRAG()
