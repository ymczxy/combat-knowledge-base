import unittest
from pathlib import Path

from ckb.content_audit import load_content_batches
from ckb.graph import load_relationships
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]

SOURCE_REVIEW_ENTITY_IDS = {
    "ckb:platform:ground:char_b1_bis",
    "ckb:platform:ground:amx_13",
    "ckb:platform:ground:amx_30",
    "ckb:platform:ground:leclerc_tank",
    "ckb:platform:ground:type_59_tank",
    "ckb:platform:ground:type_69_tank",
    "ckb:platform:ground:type_80_tank",
    "ckb:platform:ground:type_96_tank",
    "ckb:platform:ground:type_99_tank",
    "ckb:platform:ground:type_97_chi_ha",
    "ckb:platform:ground:type_61_tank",
    "ckb:platform:ground:type_74_tank",
    "ckb:platform:ground:type_90_tank",
    "ckb:platform:ground:type_10_tank",
}

SOURCE_REVIEW_RELATIONSHIP_IDS = {
    "rel:v1_6_0_batch_01:amx_30:leclerc_tank",
    "rel:v1_6_0_batch_01:type_59_tank:type_69_tank",
    "rel:v1_6_0_batch_01:type_69_tank:type_80_tank",
    "rel:v1_6_0_batch_01:type_61_tank:type_74_tank",
    "rel:v1_6_0_batch_01:type_74_tank:type_90_tank",
    "rel:v1_6_0_batch_01:type_90_tank:type_10_tank",
}


class Batch04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.batches = load_content_batches(ROOT / "data" / "content_batches")

    def test_source_review_entities_have_two_sources_and_checked_state(self):
        entity_map = {entity.id: entity for entity in self.entities}
        self.assertEqual(set(entity_map) & SOURCE_REVIEW_ENTITY_IDS, SOURCE_REVIEW_ENTITY_IDS)
        for entity_id in SOURCE_REVIEW_ENTITY_IDS:
            entity = entity_map[entity_id]
            source_keys = {
                (source.get("source_id"), source.get("url"))
                for source in entity.provenance.get("sources", [])
            }
            self.assertGreaterEqual(len(source_keys), 2, entity_id)
            self.assertEqual(entity.provenance.get("review_status"), "source_checked", entity_id)

    def test_reviewed_relationships_have_two_sources_and_checked_state(self):
        relationship_map = {relationship.id: relationship for relationship in self.relationships}
        self.assertEqual(
            set(relationship_map) & SOURCE_REVIEW_RELATIONSHIP_IDS,
            SOURCE_REVIEW_RELATIONSHIP_IDS,
        )
        for relationship_id in SOURCE_REVIEW_RELATIONSHIP_IDS:
            relationship = relationship_map[relationship_id]
            source_keys = {
                (source.get("source_id"), source.get("url"))
                for source in relationship.provenance.get("sources", [])
            }
            self.assertGreaterEqual(len(source_keys), 2, relationship_id)
            self.assertEqual(
                relationship.provenance.get("review_status"),
                "source_checked",
                relationship_id,
            )

    def test_repository_has_no_entity_embedded_relationships(self):
        remaining = {
            entity.id: entity.relationships
            for entity in self.entities
            if entity.relationships
        }
        self.assertEqual(remaining, {})

    def test_all_ground_vehicles_are_covered_by_content_batches(self):
        batched_entity_ids = {
            str(entity_id)
            for batch in self.batches
            for entity_id in batch.get("entity_ids", [])
        }
        ground_vehicle_ids = {
            entity.id
            for entity in self.entities
            if entity.entity_type == "platform"
            and entity.classification.get("class") == "GroundVehicle"
        }
        self.assertEqual(ground_vehicle_ids - batched_entity_ids, set())

    def test_akm_ammunition_relationship_is_independent(self):
        relationship_ids = {relationship.id for relationship in self.relationships}
        self.assertIn(
            "rel:v1_6_0_batch_04:akm:uses_ammunition:7_62x39",
            relationship_ids,
        )


if __name__ == "__main__":
    unittest.main()
