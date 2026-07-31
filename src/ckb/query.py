"""Stable, explicit query primitives shared by CLI, site and runtime consumers."""

from __future__ import annotations

from typing import Iterable

from .graph import KnowledgeGraph, Relationship
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


def entity_evidence(
    graph: KnowledgeGraph,
    entity_id: str,
    *,
    predicate: str | None = None,
    direction: str = "both",
) -> dict[str, object]:
    """Return an entity together with raw independent assertions and source URLs."""
    if entity_id not in graph.entities:
        raise KeyError(entity_id)
    assertions: list[Relationship] = []
    for row in graph.relationships:
        if predicate and row.predicate != predicate:
            continue
        outgoing = row.source_id == entity_id
        incoming = row.target_id == entity_id
        if direction == "out" and not outgoing:
            continue
        if direction == "in" and not incoming:
            continue
        if direction == "both" and not (outgoing or incoming):
            continue
        assertions.append(row)
    assertions.sort(key=lambda row: row.id)
    source_urls: list[str] = []
    for row in assertions:
        for source in row.provenance.get("sources", []):
            url = source.get("url") if isinstance(source, dict) else None
            if url and url not in source_urls:
                source_urls.append(str(url))
    return {
        "entity": graph.entities[entity_id].raw,
        "assertions": [row.to_dict() for row in assertions],
        "source_urls": source_urls,
    }
