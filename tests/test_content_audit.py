import unittest

from ckb.content_audit import build_content_report, validate_content_batches
from ckb.graph import Relationship
from ckb.model import Entity


def entity(entity_id: str, country: str = "american", *, complete: bool = True, source_count: int = 1) -> Entity:
    classification = {
        "domain": "Platform",
        "class": "GroundVehicle",
        "subclass": "MainBattleTank" if complete else None,
        "eras": ["CONTEMPORARY"],
        "tags": [country, "tracked", "main_battle_tank"],
    }
    return Entity.from_dict({
        "id": entity_id,
        "entity_type": "platform",
        "identity": {
            "canonical_name_en": entity_id,
            "canonical_name_zh": entity_id,
            "aliases": [],
        },
        "classification": classification,
        "relationships": [],
        "technical": {},
        "experience_profile": None,
        "gameplay": {"status": "draft"},
        "provenance": {
            "review_status": "unverified",
            "sources": [
                {"source_id": f"source_{index}", "url": f"https://example.test/{index}"}
                for index in range(source_count)
            ],
        },
        "rights": {"rights_status": "deferred"},
    })


def relationship(rel_id: str, source: str, target: str) -> Relationship:
    return Relationship.from_dict({
        "id": rel_id,
        "source_id": source,
        "predicate": "development_line_predecessor",
        "target_id": target,
        "confidence": 0.8,
        "qualifiers": {},
        "provenance": {
            "review_status": "unverified",
            "sources": [{"source_id": "source_a", "url": "https://example.test/a"}],
        },
    })


class ContentAuditTests(unittest.TestCase):
    def test_report_tracks_country_sources_completeness_and_relationship_storage(self):
        first = entity("ckb:test:first", source_count=2)
        second = entity("ckb:test:second", country="british", complete=False)
        first.relationships.append({
            "type": "development_line_predecessor",
            "target_id": second.id,
        })
        rel = relationship("rel:test:first:second", first.id, second.id)
        batches = [{
            "batch_id": "batch:test",
            "version": "1.0",
            "scope": "test",
            "entity_ids": [first.id],
            "relationship_ids": [rel.id],
        }]

        report = build_content_report([first, second], [rel], batches)

        self.assertEqual(report["entity_count"], 2)
        self.assertEqual(report["ground_vehicle_count"], 2)
        self.assertEqual(report["country_counts"], {"american": 1, "british": 1})
        self.assertEqual(report["multi_source_covered_count"], 1)
        self.assertEqual(report["missing_core_count"], 1)
        self.assertEqual(report["embedded_relationship_count"], 1)
        self.assertEqual(report["independent_relationship_count"], 1)
        self.assertEqual(report["independent_relationship_rate"], 0.5)
        self.assertEqual(report["content_batch_count"], 1)

    def test_valid_batch_accepts_complete_entities_and_known_relationships(self):
        first = entity("ckb:test:first")
        second = entity("ckb:test:second")
        rel = relationship("rel:test:first:second", first.id, second.id)
        batch = {
            "batch_id": "batch:test",
            "version": "1.0",
            "scope": "test",
            "entity_ids": [first.id, second.id],
            "relationship_ids": [rel.id],
        }

        self.assertEqual(validate_content_batches([batch], [first, second], [rel]), [])

    def test_batch_rejects_unknown_duplicate_and_incomplete_references(self):
        incomplete = entity("ckb:test:incomplete", complete=False)
        batch = {
            "batch_id": "batch:test",
            "version": "1.0",
            "scope": "test",
            "entity_ids": [incomplete.id, incomplete.id, "ckb:test:missing"],
            "relationship_ids": ["rel:test:missing"],
        }

        errors = validate_content_batches([batch], [incomplete], [])

        self.assertTrue(any("duplicate entity id" in error for error in errors))
        self.assertTrue(any("unknown entity" in error for error in errors))
        self.assertTrue(any("missing core field classification.subclass" in error for error in errors))
        self.assertTrue(any("unknown relationship" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
