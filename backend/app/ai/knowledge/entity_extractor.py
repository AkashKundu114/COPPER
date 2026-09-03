import json
import re
from typing import Any

from app.ai.knowledge.graph_store import graph_store
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.logger import logger

ATLAS_SYSTEM_PROMPT = """You are ATLAS, COPPER's Entity Extraction process. You do NOT speak to the user.

Extract entities and relationships from this conversation text.

ENTITY TYPES: PERSON, PROJECT, TECHNOLOGY, ORGANIZATION, CONCEPT, DATE_EVENT, LOCATION, FILE
RELATIONSHIP TYPES: WORKS_ON, USES, DEPENDS_ON, CREATED_BY, PART_OF, KNOWS, RELATED_TO

RULES:
1. Only extract EXPLICITLY stated or STRONGLY implied entities.
2. Normalize names to canonical form.
3. Resolve coreferences ("it", "that project" → actual entity).
4. Assign confidence 0.5–1.0.
5. If NO entities found, respond: NO_ENTITIES

FORMAT:
<entities>
[{"name": "COPPER", "type": "PROJECT", "confidence": 0.95, "context": "personal AI OS"}]
</entities>
<relationships>
[{"source": "Akash", "target": "COPPER", "type": "WORKS_ON", "confidence": 0.95}]
</relationships>"""

VALID_ENTITY_TYPES = {
    "PERSON",
    "PROJECT",
    "TECHNOLOGY",
    "ORGANIZATION",
    "CONCEPT",
    "DATE_EVENT",
    "LOCATION",
    "FILE",
}

VALID_RELATIONSHIP_TYPES = {
    "WORKS_ON",
    "USES",
    "DEPENDS_ON",
    "CREATED_BY",
    "PART_OF",
    "KNOWS",
    "RELATED_TO",
}


class EntityExtractor:
    def __init__(self):
        pass

    def get_extraction_model(self) -> str:
        """Resolves the summarizer micro-model (Qwen2.5-1.5B)."""
        return model_manager.get_model("subagents.summarizer", "qwen2.5:1.5b")

    def parse_extraction_output(self, raw_output: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Parses structured entities and relationships from the LLM output.
        Handles <entities>...</entities>, <relationships>...</relationships>, markdown fences, and NO_ENTITIES.
        """
        if not raw_output or "NO_ENTITIES" in raw_output.strip().upper():
            return [], []

        entities: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

        # 1. Parse <entities>...</entities>
        entities_match = re.search(r"<entities>(.*?)</entities>", raw_output, re.DOTALL | re.IGNORECASE)
        entities_raw = entities_match.group(1).strip() if entities_match else ""

        if entities_raw:
            entities = self._clean_and_parse_json_list(entities_raw)
        else:
            # Fallback: inspect whole text for entity-like JSON array
            array_matches = re.findall(r"\[\s*\{.*?\}\s*\]", raw_output, re.DOTALL)
            for arr_str in array_matches:
                items = self._clean_and_parse_json_list(arr_str)
                if items and isinstance(items, list) and "name" in items[0]:
                    entities = items
                    break

        # 2. Parse <relationships>...</relationships>
        rel_match = re.search(r"<relationships>(.*?)</relationships>", raw_output, re.DOTALL | re.IGNORECASE)
        rel_raw = rel_match.group(1).strip() if rel_match else ""

        if rel_raw:
            relationships = self._clean_and_parse_json_list(rel_raw)
        else:
            # Fallback: inspect for relationship-like JSON array
            array_matches = re.findall(r"\[\s*\{.*?\}\s*\]", raw_output, re.DOTALL)
            for arr_str in array_matches:
                items = self._clean_and_parse_json_list(arr_str)
                if items and isinstance(items, list) and ("source" in items[0] or "target" in items[0]):
                    relationships = items
                    break

        # 3. Sanitize and validate entities
        cleaned_entities = []
        for e in entities:
            if not isinstance(e, dict):
                continue
            name = str(e.get("name", "")).strip()
            if not name:
                continue
            etype = str(e.get("type", "CONCEPT")).strip().upper()
            if etype not in VALID_ENTITY_TYPES:
                etype = "CONCEPT"
            try:
                conf = float(e.get("confidence", 0.8))
            except (ValueError, TypeError):
                conf = 0.8
            conf = min(1.0, max(0.5, conf))

            cleaned_entities.append(
                {
                    "name": name,
                    "type": etype,
                    "confidence": conf,
                    "context": str(e.get("context", "")).strip(),
                }
            )

        # 4. Sanitize and validate relationships
        cleaned_relationships = []
        for r in relationships:
            if not isinstance(r, dict):
                continue
            src = str(r.get("source", "")).strip()
            tgt = str(r.get("target", "")).strip()
            if not src or not tgt or src.lower() == tgt.lower():
                continue
            rtype = str(r.get("type", "RELATED_TO")).strip().upper()
            if rtype not in VALID_RELATIONSHIP_TYPES:
                rtype = "RELATED_TO"
            try:
                conf = float(r.get("confidence", 0.8))
            except (ValueError, TypeError):
                conf = 0.8
            conf = min(1.0, max(0.5, conf))

            cleaned_relationships.append(
                {
                    "source": src,
                    "target": tgt,
                    "type": rtype,
                    "confidence": conf,
                    "context": str(r.get("context", "")).strip(),
                }
            )

        return cleaned_entities, cleaned_relationships

    def _clean_and_parse_json_list(self, text: str) -> list[dict[str, Any]]:
        clean = text.strip()
        # Remove markdown codeblocks ```json ... ```
        clean = re.sub(r"^```(?:json)?", "", clean, flags=re.IGNORECASE).strip()
        clean = re.sub(r"```$", "", clean).strip()

        # Find array boundaries
        start = clean.find("[")
        end = clean.rfind("]")
        if start != -1 and end != -1 and end > start:
            clean = clean[start : end + 1]

        try:
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
        except Exception as e:
            # Handle trailing commas or minor JSON errors
            try:
                fixed = re.sub(r",\s*([\]}])", r"\1", clean)
                parsed = json.loads(fixed)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                logger.debug(f"[ATLAS Extractor] Failed to parse JSON list from: {text[:100]} (err: {e})")

        return []

    async def extract_from_text(self, text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Executes entity and relationship extraction on conversational text using the local LLM.
        """
        if not text or len(text.strip()) < 5:
            return [], []

        model = self.get_extraction_model()
        messages = [
            {"role": "system", "content": ATLAS_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract entities and relationships from this text:\n\n{text}"},
        ]

        try:
            raw_response = await ollama_client.chat(messages, model=model)
            return self.parse_extraction_output(raw_response)
        except Exception as e:
            logger.warning(f"[ATLAS Extractor] Extraction failed via {model}: {e}")
            return [], []

    async def extract_and_store(self, text: str, session_id: str | None = None) -> dict[str, Any]:
        """
        Extracts entities and relationships from conversation text and persists them into GraphStore.
        """
        entities, relationships = await self.extract_from_text(text)
        stored_entities = []
        stored_relationships = []

        meta = {"session_id": session_id} if session_id else {}

        for ent in entities:
            try:
                saved_ent = graph_store.add_entity(
                    name=ent["name"],
                    entity_type=ent["type"],
                    confidence=ent["confidence"],
                    context=ent.get("context", ""),
                    metadata=meta,
                )
                stored_entities.append(saved_ent)
            except Exception as err:
                logger.warning(f"[ATLAS Extractor] Failed to save entity {ent}: {err}")

        for rel in relationships:
            try:
                saved_rel = graph_store.add_relationship(
                    source_name=rel["source"],
                    target_name=rel["target"],
                    relation_type=rel["type"],
                    confidence=rel["confidence"],
                    context=rel.get("context", ""),
                    metadata=meta,
                )
                stored_relationships.append(saved_rel)
            except Exception as err:
                logger.warning(f"[ATLAS Extractor] Failed to save relationship {rel}: {err}")

        if stored_entities or stored_relationships:
            logger.info(
                f"[ATLAS Extractor] Stored {len(stored_entities)} entities, "
                f"{len(stored_relationships)} relationships from text turn."
            )

        return {
            "entities": stored_entities,
            "relationships": stored_relationships,
        }


entity_extractor = EntityExtractor()
