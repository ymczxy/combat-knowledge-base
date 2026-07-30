"""Stable, explicit query primitives shared by CLI, site and runtime consumers."""

from __future__ import annotations

from typing import Iterable

from .graph import KnowledgeGraph
from .model import Entity


def search_entities(
    entities: Iterable[Entity],
    *,
    text: str | None = None,
    entity_type: str | None = None,
    domain: str | None = None,
    era: str | None = None,
    limit: int = 50,
) -> list[Entity]:
    if limit < 1:
        raise ValueError("limit must be positive")
    needle = text.casefold().strip() if text else None
    rows: list[Entity] = []
    for entity in entities:
        classification = entity.classification
        haystack = " ".join([
            entity.name_en,
            entity.name_zh,
            *entity.aliases,
            *[str(value) for value in classification.get("tags", [])],
        ]).casefold()
        if needle and needle not in haystack:
            continue
        if entity_type and entity.entity_type != entity_type:
            continue
        if domain and str(classification.get("domain", "")).casefold() != domain.casefold():
            continue
        if era and era not in classification.get("eras", []):
            continue
        rows.append(entity)
    rows.sort(key=lambda entity: (entity.name_en.casefold(), entity.id))
    return rows[:limit]


def related_entities(graph: KnowledgeGraph, entity_id: str, predicate: str | None = None, direction: str = "both") -> list[Entity]:
    rows = graph.neighbors(entity_id, predicate=predicate, direction=direction)
    target_ids: list[str] = []
    for relation in rows:
        target = relation.target_id if relation.source_id == entity_id else relation.source_id
        if target not in target_ids:
            target_ids.append(target)
    return [graph.entities[target_id] for target_id in target_ids if target_id in graph.entities]
