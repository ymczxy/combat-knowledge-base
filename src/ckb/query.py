"""Stable, explicit query primitives shared by CLI, site and runtime consumers."""

from __future__ import annotations

from typing import Any, Iterable

from .assertions import aggregate_assertions
from .graph import KnowledgeGraph, Relationship
from .model import Entity


QUERY_CONTRACT_VERSION = "1.1"


def search_entities(
    entities: Iterable[Entity],
    *,
    text: str | None = None,
    entity_type: str | None = None,
    domain: str | None = None,
    entity_class: str | None = None,
    subclass: str | None = None,
    era: str | None = None,
    tag: str | None = None,
    review_status: str | None = None,
    technical_field: str | None = None,
    minimum_sources: int = 0,
    has_technical: bool | None = None,
    limit: int = 50,
) -> list[Entity]:
    if limit < 1:
        raise ValueError("limit must be positive")
    if minimum_sources < 0:
        raise ValueError("minimum_sources must be non-negative")
    needle = text.casefold().strip() if text else None
    rows: list[Entity] = []
    for entity in entities:
        classification = entity.classification
        claims = entity.technical.get("claims", []) if isinstance(entity.technical, dict) else []
        claim_fields = {
            str(claim.get("field", "")).casefold()
            for claim in claims
            if isinstance(claim, dict)
        }
        source_count = len(
            {
                (str(source.get("source_id", "")), str(source.get("url", "")))
                for source in entity.provenance.get("sources", [])
                if isinstance(source, dict)
            }
        )
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
        if entity_class and str(classification.get("class", "")).casefold() != entity_class.casefold():
            continue
        if subclass and str(classification.get("subclass", "")).casefold() != subclass.casefold():
            continue
        if era and era not in classification.get("eras", []):
            continue
        if tag and tag.casefold() not in {
            str(value).casefold() for value in classification.get("tags", [])
        }:
            continue
        if review_status and str(entity.provenance.get("review_status", "")).casefold() != review_status.casefold():
            continue
        if technical_field and technical_field.casefold() not in claim_fields:
            continue
        if source_count < minimum_sources:
            continue
        if has_technical is not None and bool(claims) is not has_technical:
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
        "query_contract_version": QUERY_CONTRACT_VERSION,
        "entity": graph.entities[entity_id].raw,
        "assertions": [row.to_dict() for row in assertions],
        "source_urls": source_urls,
    }


def fact_evidence(graph: KnowledgeGraph, fact_id: str) -> dict[str, Any]:
    """Resolve one canonical fact back to every raw assertion and cited source."""
    report = aggregate_assertions(graph.relationships, graph.predicate_registry)
    fact = next((row for row in report.facts if row.id == fact_id), None)
    if fact is None:
        raise KeyError(fact_id)
    assertion_map = {row.id: row for row in graph.relationships}
    assertions = [
        assertion_map[assertion_id].to_dict()
        for assertion_id in fact.assertion_ids
        if assertion_id in assertion_map
    ]
    source_urls = [
        str(source.get("url"))
        for source in fact.sources
        if isinstance(source, dict) and source.get("url")
    ]
    return {
        "query_contract_version": QUERY_CONTRACT_VERSION,
        "fact": fact.to_dict(),
        "assertions": assertions,
        "source_urls": source_urls,
    }
