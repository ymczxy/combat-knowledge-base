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


def relationship(rel_id: str, source: str, target: str, *, source_count: int = 1) -> Relationship:
    return Relationship.from_dict({
        "id": rel_id,
        "source_id": source,
        "predicate": "development_line_predecessor",
        "target_id": target,
        "confidence": 0.8,
        "qualifiers": {},
        "provenance": {
            "review_status": "source_checked" if source_count >= 2 else "unverified",
            "sources": [
                {"source_id": f"source_{index}", "url": f"https://example.test/rel/{index}"}
                for index in range(source_count)
            ],
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
        rel = relationship("rel:test:first:second", first.id, second.id, source_count=2)
        batches = [{
            "batch_id": "batch:test",
            "version": "1.0",
            "scope": "test",
            "entity_ids": [first.id],
            "relationship_ids": [rel.id],
        }]

        report = build_content_report([first, second], [rel], batches)

        self.assertEqual(report["report_version"], "1.1")
        self.assertEqual(report["entity_count"], 2)
        self.assertEqual(report["ground_vehicle_count"], 2)
        self.assertEqual(report["country_counts"], {"american": 1, "british": 1})
        self.assertEqual(report["multi_source_covered_count"], 1)
        self.assertEqual(report["missing_core_count"], 1)
        self.assertEqual(report["embedded_relationship_count"], 1)
        self.assertEqual(report["independent_relationship_count"], 1)
        self.assertEqual(report["independent_relationship_rate"], 0.5)
        self.assertEqual(report["relationship_review_status_counts"], {"source_checked": 1})
        self.assertEqual(report["relationship_source_covered_count"], 1)
        self.assertEqual(report["relationship_multi_source_covered_count"], 1)
        self.assertEqual(report["relationship_multi_source_coverage_rate"], 1.0)
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

    def test_batch_enforces_minimum_independent_entity_source_count(self):
        one_source = entity("ckb:test:one", source_count=1)
        two_sources = entity("ckb:test:two", source_count=2)
        batch = {
            "batch_id": "batch:source-review",
            "version": "1.0",
            "scope": "source review",
            "entity_ids": [one_source.id, two_sources.id],
            "relationship_ids": [],
            "quality_targets": {"minimum_sources_per_entity": 2},
        }

        errors = validate_content_batches([batch], [one_source, two_sources], [])

        self.assertEqual(len(errors), 1)
        self.assertIn("ckb:test:one has 1 independent sources; requires at least 2", errors[0])

    def test_batch_enforces_minimum_independent_relationship_source_count(self):
        first = entity("ckb:test:first")
        second = entity("ckb:test:second")
        one_source = relationship("rel:test:one", first.id, second.id, source_count=1)
        two_sources = relationship("rel:test:two", second.id, first.id, source_count=2)
        batch = {
            "batch_id": "batch:relationship-review",
            "version": "1.0",
            "scope": "relationship source review",
            "entity_ids": [first.id, second.id],
            "relationship_ids": [one_source.id, two_sources.id],
            "quality_targets": {"minimum_sources_per_relationship": 2},
        }

        errors = validate_content_batches([batch], [first, second], [one_source, two_sources])

        self.assertEqual(len(errors), 1)
        self.assertIn("rel:test:one has 1 independent sources; requires at least 2", errors[0])

    def test_invalid_source_target_is_rejected(self):
        row = entity("ckb:test:row")
        batch = {
            "batch_id": "batch:bad-source-target",
            "version": "1.0",
            "scope": "test",
            "entity_ids": [row.id],
            "relationship_ids": [],
            "quality_targets": {"minimum_sources_per_entity": "not-an-integer"},
        }

        errors = validate_content_batches([batch], [row], [])

        self.assertTrue(any("minimum_sources_per_entity must be an integer" in error for error in errors))

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
