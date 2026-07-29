from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
import json

from .model import Entity


@dataclass(frozen=True, slots=True)
class Relationship:
    id: str
    source_id: str
    predicate: str
    target_id: str
    provenance: dict[str, Any]
    confidence: float = 1.0
    qualifiers: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        return cls(
            id=str(data["id"]),
            source_id=str(data["source_id"]),
            predicate=str(data["predicate"]),
            target_id=str(data["target_id"]),
            confidence=float(data.get("confidence", 1.0)),
            provenance=dict(data.get("provenance", {})),
            qualifiers=dict(data.get("qualifiers", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "predicate": self.predicate,
            "target_id": self.target_id,
            "confidence": self.confidence,
            "qualifiers": self.qualifiers,
            "provenance": self.provenance,
        }


def embedded_relationships(entities: Iterable[Entity]) -> list[Relationship]:
    rows: list[Relationship] = []
    for entity in entities:
        for index, relation in enumerate(entity.relationships):
            target_id = relation.get("target_id")
            predicate = relation.get("type") or relation.get("predicate")
            if not target_id or not predicate:
                continue
            rows.append(Relationship(
                id=f"rel:embedded:{entity.id.replace(':', '_')}:{index}",
                source_id=entity.id,
                predicate=str(predicate),
                target_id=str(target_id),
                confidence=float(relation.get("confidence", 1.0)),
                qualifiers=dict(relation.get("qualifiers", {})),
                provenance=dict(relation.get("provenance", entity.provenance)),
            ))
    return rows


def load_relationships(root: Path) -> list[Relationship]:
    rows: list[Relationship] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else [payload]
        rows.extend(Relationship.from_dict(item) for item in items if isinstance(item, dict))
    return rows


class KnowledgeGraph:
    def __init__(self, entities: Iterable[Entity], relationships: Iterable[Relationship]):
        self.entities = {entity.id: entity for entity in entities}
        self.relationships = list(relationships)
        self.outgoing: dict[str, list[Relationship]] = defaultdict(list)
        self.incoming: dict[str, list[Relationship]] = defaultdict(list)
        for relation in self.relationships:
            self.outgoing[relation.source_id].append(relation)
            self.incoming[relation.target_id].append(relation)

    def neighbors(self, entity_id: str, predicate: str | None = None, direction: str = "both") -> list[Relationship]:
        rows: list[Relationship] = []
        if direction in {"out", "both"}:
            rows.extend(self.outgoing.get(entity_id, []))
        if direction in {"in", "both"}:
            rows.extend(self.incoming.get(entity_id, []))
        if predicate is not None:
            rows = [row for row in rows if row.predicate == predicate]
        return rows

    def shortest_path(self, source_id: str, target_id: str, max_depth: int = 8) -> list[Relationship]:
        if source_id == target_id:
            return []
        queue = deque([(source_id, [])])
        visited = {source_id}
        while queue:
            current, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for relation in self.outgoing.get(current, []):
                next_id = relation.target_id
                next_path = [*path, relation]
                if next_id == target_id:
                    return next_path
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, next_path))
        return []

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        for relation in self.relationships:
            if relation.id in seen:
                errors.append(f"{relation.id}: duplicate relationship id")
            seen.add(relation.id)
            if relation.source_id not in self.entities:
                errors.append(f"{relation.id}: missing source entity {relation.source_id}")
            if relation.target_id not in self.entities:
                errors.append(f"{relation.id}: missing target entity {relation.target_id}")
            if not relation.predicate:
                errors.append(f"{relation.id}: missing predicate")
            if not 0 <= relation.confidence <= 1:
                errors.append(f"{relation.id}: confidence outside [0, 1]")
            if not relation.provenance.get("review_status"):
                errors.append(f"{relation.id}: missing provenance.review_status")
        return errors

    def to_bundle(self) -> dict[str, Any]:
        return {
            "graph_version": "1.0",
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "entities": [entity.raw for entity in self.entities.values()],
            "relationships": [relation.to_dict() for relation in self.relationships],
        }
