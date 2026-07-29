from ckb.graph import KnowledgeGraph, Relationship
from ckb.model import Entity


def entity(entity_id: str) -> Entity:
    return Entity.from_dict({
        "id": entity_id,
        "entity_type": "platform",
        "identity": {"canonical_name_en": entity_id, "canonical_name_zh": entity_id, "aliases": []},
        "classification": {"domain": "Platform", "class": "GroundVehicle"},
        "provenance": {"review_status": "unverified", "sources": []},
    })


def relation(rel_id: str, source: str, target: str) -> Relationship:
    return Relationship.from_dict({
        "id": rel_id,
        "source_id": source,
        "predicate": "developed_into",
        "target_id": target,
        "confidence": 0.9,
        "provenance": {"review_status": "unverified", "sources": []},
    })


def test_neighbors_and_shortest_path():
    a, b, c = entity("ckb:test:a"), entity("ckb:test:b"), entity("ckb:test:c")
    ab = relation("rel:test:a:b", a.id, b.id)
    bc = relation("rel:test:b:c", b.id, c.id)
    graph = KnowledgeGraph([a, b, c], [ab, bc])

    assert graph.validate() == []
    assert graph.neighbors(a.id, direction="out") == [ab]
    assert graph.shortest_path(a.id, c.id) == [ab, bc]


def test_missing_target_and_invalid_confidence_are_rejected():
    a = entity("ckb:test:a")
    bad = Relationship.from_dict({
        "id": "rel:test:bad",
        "source_id": a.id,
        "predicate": "uses_engine",
        "target_id": "ckb:test:missing",
        "confidence": 1.2,
        "provenance": {"review_status": "unverified", "sources": []},
    })
    errors = KnowledgeGraph([a], [bad]).validate()

    assert any("missing target entity" in error for error in errors)
    assert any("confidence outside" in error for error in errors)
