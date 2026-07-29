from pathlib import Path

from ckb.graph import KnowledgeGraph, Relationship
from ckb.model import Entity
from ckb.predicates import PredicateRegistry, load_predicate_registry


ROOT = Path(__file__).resolve().parents[1]


def entity(entity_id: str, entity_type: str = "platform", class_name: str = "GroundVehicle") -> Entity:
    return Entity.from_dict({
        "id": entity_id,
        "entity_type": entity_type,
        "identity": {"canonical_name_en": entity_id, "canonical_name_zh": entity_id, "aliases": []},
        "classification": {"domain": entity_type.title(), "class": class_name},
        "provenance": {"review_status": "unverified", "sources": []},
    })


def relation(rel_id: str, source: str, predicate: str, target: str) -> Relationship:
    return Relationship.from_dict({
        "id": rel_id,
        "source_id": source,
        "predicate": predicate,
        "target_id": target,
        "confidence": 0.9,
        "provenance": {"review_status": "unverified", "sources": []},
    })


def registry() -> PredicateRegistry:
    return PredicateRegistry.from_dict({
        "registry_version": "test",
        "predicates": [
            {
                "name": "development_line_predecessor",
                "labels": {"en": "predecessor", "zh": "前身"},
                "description": {"en": "Earlier design.", "zh": "更早设计。"},
                "inverse": "development_line_successor",
                "transitive": True,
                "source_entity_types": ["platform"],
                "target_entity_types": ["platform"],
            },
            {
                "name": "development_line_successor",
                "labels": {"en": "successor", "zh": "后继"},
                "description": {"en": "Later design.", "zh": "更晚设计。"},
                "inverse": "development_line_predecessor",
                "transitive": True,
                "source_entity_types": ["platform"],
                "target_entity_types": ["platform"],
            },
            {
                "name": "contemporary",
                "labels": {"en": "contemporary", "zh": "同期"},
                "description": {"en": "Overlapping period.", "zh": "时期重叠。"},
                "inverse": "contemporary",
                "symmetric": True,
            },
            {
                "name": "uses_ammunition",
                "labels": {"en": "uses ammunition", "zh": "使用弹药"},
                "description": {"en": "Uses ammunition.", "zh": "使用弹药。"},
                "inverse": "ammunition_used_by",
                "source_entity_types": ["weapon"],
                "target_entity_types": ["ammunition"],
            },
            {
                "name": "ammunition_used_by",
                "labels": {"en": "used by", "zh": "被使用"},
                "description": {"en": "Used by a weapon.", "zh": "被武器使用。"},
                "inverse": "uses_ammunition",
                "source_entity_types": ["ammunition"],
                "target_entity_types": ["weapon"],
            },
        ],
    })


def test_repository_predicate_registry_is_internally_consistent():
    loaded = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    assert loaded.validate() == []
    assert loaded.inverse_of("uses_ammunition") == "ammunition_used_by"
    assert loaded.inverse_of("contemporary") == "contemporary"


def test_inverse_symmetric_and_transitive_resolution():
    a, b, c = entity("ckb:test:a"), entity("ckb:test:b"), entity("ckb:test:c")
    ab = relation("rel:test:a:b", a.id, "development_line_predecessor", b.id)
    bc = relation("rel:test:b:c", b.id, "development_line_predecessor", c.id)
    contemporary = relation("rel:test:a:c:contemporary", a.id, "contemporary", c.id)
    graph = KnowledgeGraph([a, b, c], [ab, bc, contemporary], predicate_registry=registry())

    assert graph.validate() == []
    inverse = graph.related(b.id, "development_line_successor")
    assert [row.target_id for row in inverse] == [a.id]
    assert inverse[0].inferred_from_inverse is True
    assert [row.target_id for row in graph.related(c.id, "contemporary")] == [a.id]
    assert graph.transitive_targets(a.id, "development_line_predecessor") == [b.id, c.id]


def test_unknown_predicate_and_endpoint_type_are_rejected():
    weapon = entity("ckb:test:weapon", "weapon", "Firearm")
    wrong_target = entity("ckb:test:platform", "platform", "GroundVehicle")
    wrong_type = relation(
        "rel:test:wrong_type",
        weapon.id,
        "uses_ammunition",
        wrong_target.id,
    )
    unknown = relation(
        "rel:test:unknown",
        weapon.id,
        "invented_relation",
        wrong_target.id,
    )
    errors = KnowledgeGraph(
        [weapon, wrong_target],
        [wrong_type, unknown],
        predicate_registry=registry(),
    ).validate()

    assert any("rejects target entity_type" in error for error in errors)
    assert any("unknown predicate invented_relation" in error for error in errors)
