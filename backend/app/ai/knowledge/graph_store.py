import asyncio
import logging
from typing import Any

import networkx as nx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.database.models.knowledge_graph import KnowledgeEntity, KnowledgeRelationship
from app.database.postgres import SessionLocal


def canonicalize_name(name: str) -> str:
    """Normalize names to canonical form (stripped, single spaced, lowercased)."""
    return " ".join(name.strip().split()).lower() if name else ""


def bayesian_confidence_update(prior: float, incoming: float, learning_rate: float = 0.4) -> float:
    """
    Bayesian confidence reinforcement using independent confirmation model (Noisy-OR).
    Increases confidence when repeatedly confirmed, bounded in [0.5, 0.99].
    """
    p_prior = max(0.01, min(0.99, float(prior)))
    p_incoming = max(0.01, min(0.99, float(incoming)))
    p_error = (1.0 - p_prior) * (1.0 - learning_rate * p_incoming)
    updated = 1.0 - p_error
    return round(min(0.99, max(0.5, updated)), 3)


class GraphStore:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._lock = asyncio.Lock()
        self._initialized = False

    def initialize_sync(self):
        """Loads all entities and relationships from SQLite into the NetworkX graph."""
        db: Session = SessionLocal()
        try:
            self.graph.clear()
            entities = db.query(KnowledgeEntity).all()
            for entity in entities:
                self._add_node_to_graph(entity)

            relationships = db.query(KnowledgeRelationship).all()
            for rel in relationships:
                self._add_edge_to_graph(rel)

            self._initialized = True
            logger.info(
                f"[ATLAS GraphStore] Loaded {len(entities)} entities and {len(relationships)} relationships into NetworkX."
            )
        except Exception as e:
            logger.error(f"[ATLAS GraphStore] Failed to initialize from DB: {e}")
        finally:
            db.close()

    def _ensure_initialized(self):
        if not self._initialized:
            self.initialize_sync()

    def _add_node_to_graph(self, entity: KnowledgeEntity):
        canon = entity.canonical_name
        self.graph.add_node(
            canon,
            id=entity.id,
            name=entity.name,
            canonical_name=canon,
            type=entity.entity_type,
            confidence=entity.confidence,
            context=entity.context or "",
            evidence_count=entity.evidence_count,
            metadata=entity.extra_metadata or {},
        )

    def _add_edge_to_graph(self, rel: KnowledgeRelationship):
        source_canon = canonicalize_name(rel.source_name)
        target_canon = canonicalize_name(rel.target_name)
        # Add edge with unique key (rel.relation_type, rel.id)
        edge_key = f"{rel.relation_type}:{rel.id}"
        self.graph.add_edge(
            source_canon,
            target_canon,
            key=edge_key,
            id=rel.id,
            source=rel.source_name,
            target=rel.target_name,
            type=rel.relation_type,
            confidence=rel.confidence,
            context=rel.context or "",
            evidence_count=rel.evidence_count,
            metadata=rel.extra_metadata or {},
        )

    def add_entity(
        self,
        name: str,
        entity_type: str = "CONCEPT",
        confidence: float = 0.8,
        context: str = "",
        metadata: dict | None = None,
        db: Session | None = None,
    ) -> dict:
        """
        Adds or updates an entity. If canonical name exists, merges with Bayesian confidence update.
        """
        self._ensure_initialized()
        name_clean = name.strip()
        if not name_clean:
            raise ValueError("Entity name cannot be empty.")

        canon = canonicalize_name(name_clean)
        clean_type = entity_type.strip().upper() if entity_type else "CONCEPT"
        conf = min(0.99, max(0.5, float(confidence)))

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            existing = db.query(KnowledgeEntity).filter(KnowledgeEntity.canonical_name == canon).first()
            if existing:
                # Deduplicate: update confidence and evidence count
                new_conf = bayesian_confidence_update(existing.confidence, conf)
                existing.confidence = new_conf
                existing.evidence_count += 1
                if context and (not existing.context or len(context) > len(existing.context)):
                    existing.context = context
                if clean_type != "CONCEPT" and existing.entity_type == "CONCEPT":
                    existing.entity_type = clean_type
                if metadata:
                    meta = existing.extra_metadata or {}
                    meta.update(metadata)
                    existing.extra_metadata = meta

                db.commit()
                db.refresh(existing)
                self._add_node_to_graph(existing)
                return existing.to_dict()
            else:
                new_entity = KnowledgeEntity(
                    name=name_clean,
                    canonical_name=canon,
                    entity_type=clean_type,
                    confidence=conf,
                    context=context or "",
                    evidence_count=1,
                    extra_metadata=metadata or {},
                )
                db.add(new_entity)
                db.commit()
                db.refresh(new_entity)
                self._add_node_to_graph(new_entity)
                return new_entity.to_dict()
        finally:
            if close_db:
                db.close()

    def add_relationship(
        self,
        source_name: str,
        target_name: str,
        relation_type: str = "RELATED_TO",
        confidence: float = 0.8,
        context: str = "",
        metadata: dict | None = None,
        db: Session | None = None,
    ) -> dict:
        """
        Adds or updates a relationship between source and target entities.
        Ensures both entities exist, then applies Bayesian confidence reinforcement if already present.
        """
        self._ensure_initialized()
        src_clean = source_name.strip()
        tgt_clean = target_name.strip()
        if not src_clean or not tgt_clean:
            raise ValueError("Source and target entity names cannot be empty.")

        src_canon = canonicalize_name(src_clean)
        tgt_canon = canonicalize_name(tgt_clean)
        rel_type_clean = relation_type.strip().upper() if relation_type else "RELATED_TO"
        conf = min(0.99, max(0.5, float(confidence)))

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            # Ensure source and target entities exist
            src_entity = self.add_entity(name=src_clean, entity_type="CONCEPT", confidence=conf, db=db)
            tgt_entity = self.add_entity(name=tgt_clean, entity_type="CONCEPT", confidence=conf, db=db)

            existing_rel = (
                db.query(KnowledgeRelationship)
                .filter(
                    KnowledgeRelationship.source_name == src_clean,
                    KnowledgeRelationship.target_name == tgt_clean,
                    KnowledgeRelationship.relation_type == rel_type_clean,
                )
                .first()
            )

            if not existing_rel:
                # Also check case-insensitive match on canonical names
                candidates = (
                    db.query(KnowledgeRelationship)
                    .filter(KnowledgeRelationship.relation_type == rel_type_clean)
                    .all()
                )
                for cand in candidates:
                    if (
                        canonicalize_name(cand.source_name) == src_canon
                        and canonicalize_name(cand.target_name) == tgt_canon
                    ):
                        existing_rel = cand
                        break

            if existing_rel:
                new_conf = bayesian_confidence_update(existing_rel.confidence, conf)
                existing_rel.confidence = new_conf
                existing_rel.evidence_count += 1
                if context and (not existing_rel.context or len(context) > len(existing_rel.context)):
                    existing_rel.context = context
                if metadata:
                    meta = existing_rel.extra_metadata or {}
                    meta.update(metadata)
                    existing_rel.extra_metadata = meta

                db.commit()
                db.refresh(existing_rel)
                self._add_edge_to_graph(existing_rel)
                return existing_rel.to_dict()
            else:
                new_rel = KnowledgeRelationship(
                    source_id=src_entity["id"],
                    target_id=tgt_entity["id"],
                    source_name=src_entity["name"],
                    target_name=tgt_entity["name"],
                    relation_type=rel_type_clean,
                    confidence=conf,
                    context=context or "",
                    evidence_count=1,
                    extra_metadata=metadata or {},
                )
                db.add(new_rel)
                db.commit()
                db.refresh(new_rel)
                self._add_edge_to_graph(new_rel)
                return new_rel.to_dict()
        finally:
            if close_db:
                db.close()

    def query_entity(self, name_or_id: str | int) -> dict | None:
        """Looks up an entity by name or integer ID."""
        self._ensure_initialized()
        if isinstance(name_or_id, int) or (isinstance(name_or_id, str) and name_or_id.isdigit()):
            target_id = int(name_or_id)
            for node, data in self.graph.nodes(data=True):
                if data.get("id") == target_id:
                    return data
            # Fallback to DB
            db = SessionLocal()
            try:
                e = db.query(KnowledgeEntity).filter(KnowledgeEntity.id == target_id).first()
                return e.to_dict() if e else None
            finally:
                db.close()

        canon = canonicalize_name(str(name_or_id))
        if canon in self.graph:
            return self.graph.nodes[canon]

        db = SessionLocal()
        try:
            e = db.query(KnowledgeEntity).filter(KnowledgeEntity.canonical_name == canon).first()
            return e.to_dict() if e else None
        finally:
            db.close()

    def query_neighbors(self, name: str, depth: int = 1, min_confidence: float = 0.0) -> dict:
        """
        Retrieves local neighborhood up to `depth` hops around an entity.
        Returns nodes and edges filtered by `min_confidence`.
        """
        self._ensure_initialized()
        canon = canonicalize_name(name)
        if canon not in self.graph:
            return {"nodes": [], "edges": [], "links": []}

        # Use undirected view to traverse edges in both directions
        undirected = self.graph.to_undirected(as_view=True)
        subgraph_nodes = set([canon])

        current_level = set([canon])
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                for neighbor in undirected.neighbors(node):
                    if neighbor not in subgraph_nodes:
                        next_level.add(neighbor)
            subgraph_nodes.update(next_level)
            current_level = next_level

        # Extract nodes and filter by min_confidence
        nodes = []
        valid_node_keys = set()
        for node_key in subgraph_nodes:
            node_data = dict(self.graph.nodes[node_key])
            if node_data.get("confidence", 0.0) >= min_confidence:
                nodes.append(node_data)
                valid_node_keys.add(node_key)

        # Extract edges connecting these valid nodes
        edges = []
        for u, v, key, edge_data in self.graph.edges(keys=True, data=True):
            if u in valid_node_keys and v in valid_node_keys:
                if edge_data.get("confidence", 0.0) >= min_confidence:
                    edge_dict = dict(edge_data)
                    edges.append(edge_dict)

        # Sort nodes and edges by confidence descending
        nodes.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        edges.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        return {
            "center": canon,
            "nodes": nodes,
            "edges": edges,
            "links": edges,  # D3.js alias
        }

    def find_path(self, source: str, target: str) -> list[dict] | None:
        """
        Computes the shortest path between two entities in the graph.
        Returns a sequential list of path step dictionaries containing entities and relationships.
        """
        self._ensure_initialized()
        src_canon = canonicalize_name(source)
        tgt_canon = canonicalize_name(target)

        if src_canon not in self.graph or tgt_canon not in self.graph:
            return None

        try:
            undirected = self.graph.to_undirected(as_view=True)
            path_nodes = nx.shortest_path(undirected, source=src_canon, target=tgt_canon)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        path_steps = []
        for i in range(len(path_nodes)):
            curr_node = path_nodes[i]
            node_info = dict(self.graph.nodes[curr_node])
            step = {"step": i + 1, "entity": node_info, "relationship_to_next": None}

            if i < len(path_nodes) - 1:
                next_node = path_nodes[i + 1]
                # Check edges in both directions
                forward_edges = self.graph.get_edge_data(curr_node, next_node) or {}
                backward_edges = self.graph.get_edge_data(next_node, curr_node) or {}

                best_edge = None
                best_conf = -1.0
                for edge_key, data in {**forward_edges, **backward_edges}.items():
                    if data.get("confidence", 0) > best_conf:
                        best_conf = data.get("confidence", 0)
                        best_edge = dict(data)

                step["relationship_to_next"] = best_edge

            path_steps.append(step)

        return path_steps

    def get_subgraph(self, entity_name: str | None = None, depth: int = 1, max_nodes: int = 30) -> dict:
        """
        Generates a D3.js-ready force-directed graph structure.
        If `entity_name` is provided, generates an ego-graph; otherwise returns top entities.
        """
        self._ensure_initialized()
        if entity_name:
            result = self.query_neighbors(entity_name, depth=depth, min_confidence=0.0)
            nodes = result["nodes"][:max_nodes]
            node_names = set(n["canonical_name"] for n in nodes)
            edges = [e for e in result["edges"] if canonicalize_name(e["source"]) in node_names and canonicalize_name(e["target"]) in node_names]
            return {
                "nodes": nodes,
                "edges": edges,
                "links": edges,
            }

        # Global graph top subgraph
        nodes = [dict(data) for _, data in self.graph.nodes(data=True)]
        nodes.sort(key=lambda x: (x.get("evidence_count", 1), x.get("confidence", 0.0)), reverse=True)
        top_nodes = nodes[:max_nodes]
        top_node_canons = set(n["canonical_name"] for n in top_nodes)

        edges = []
        for u, v, key, edge_data in self.graph.edges(keys=True, data=True):
            if u in top_node_canons and v in top_node_canons:
                edges.append(dict(edge_data))

        edges.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        return {
            "nodes": top_nodes,
            "edges": edges,
            "links": edges,
        }

    def remove_entity(self, entity_id: int) -> bool:
        """
        Deletes an entity and its associated relationships from SQLite and NetworkX.
        """
        self._ensure_initialized()
        db = SessionLocal()
        try:
            entity = db.query(KnowledgeEntity).filter(KnowledgeEntity.id == entity_id).first()
            if not entity:
                return False

            canon = entity.canonical_name
            # Delete relationships connected to this entity
            db.query(KnowledgeRelationship).filter(
                or_(
                    KnowledgeRelationship.source_id == entity_id,
                    KnowledgeRelationship.target_id == entity_id,
                    KnowledgeRelationship.source_name == entity.name,
                    KnowledgeRelationship.target_name == entity.name,
                )
            ).delete()

            db.delete(entity)
            db.commit()

            # Remove from NetworkX
            if canon in self.graph:
                self.graph.remove_node(canon)

            logger.info(f"[ATLAS GraphStore] Deleted entity {entity.name} (id={entity_id}) and connected edges.")
            return True
        except Exception as e:
            logger.error(f"[ATLAS GraphStore] Error deleting entity {entity_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def list_entities(
        self,
        entity_type: str | None = None,
        min_confidence: float = 0.0,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Lists entities from DB with filtering and confidence-based ordering."""
        db = SessionLocal()
        try:
            query = db.query(KnowledgeEntity).filter(KnowledgeEntity.confidence >= min_confidence)
            if entity_type:
                query = query.filter(KnowledgeEntity.entity_type == entity_type.strip().upper())
            if search:
                query = query.filter(KnowledgeEntity.name.ilike(f"%{search.strip()}%"))

            entities = (
                query.order_by(KnowledgeEntity.confidence.desc(), KnowledgeEntity.evidence_count.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [e.to_dict() for e in entities]
        finally:
            db.close()

    def list_relationships(
        self,
        relation_type: str | None = None,
        source: str | None = None,
        target: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Lists relationships from DB with filtering and confidence-based ordering."""
        db = SessionLocal()
        try:
            query = db.query(KnowledgeRelationship).filter(KnowledgeRelationship.confidence >= min_confidence)
            if relation_type:
                query = query.filter(KnowledgeRelationship.relation_type == relation_type.strip().upper())
            if source:
                query = query.filter(KnowledgeRelationship.source_name.ilike(f"%{source.strip()}%"))
            if target:
                query = query.filter(KnowledgeRelationship.target_name.ilike(f"%{target.strip()}%"))

            rels = (
                query.order_by(KnowledgeRelationship.confidence.desc(), KnowledgeRelationship.evidence_count.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [r.to_dict() for r in rels]
        finally:
            db.close()

    def get_stats(self) -> dict:
        """Returns statistics of entities and relationships in the knowledge graph."""
        self._ensure_initialized()
        node_types: dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("type", "CONCEPT")
            node_types[t] = node_types.get(t, 0) + 1

        rel_types: dict[str, int] = {}
        for _, _, _, data in self.graph.edges(keys=True, data=True):
            r = data.get("type", "RELATED_TO")
            rel_types[r] = rel_types.get(r, 0) + 1

        return {
            "total_entities": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "entities_by_type": node_types,
            "relationships_by_type": rel_types,
        }


graph_store = GraphStore()
