import unittest
from pathlib import Path

from ckb.content_audit import load_content_batches
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.technical import build_technical_comparison

ROOT = Path(__file__).resolve().parents[1]
ENTITY_IDS = {"ckb:weapon:firearm:karabiner_98k", "ckb:ammunition:cartridge:8x57_is"}
RELATIONSHIP_ID = "rel:v1_6_1_batch_04:karabiner_98k:uses_ammunition:8x57_is"

class SmallArmsBatch04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.batches = load_content_batches(ROOT / "data" / "content_batches")
        cls.entity_map = {entity.id: entity for entity in cls.entities}
        cls.relationship_map = {relationship.id: relationship for relationship in cls.relationships}

    def test_batch_registers_two_entities_and_relation(self):
        batch = next(row for row in self.batches if row.get("batch_id") == "v1.6.1-small-arms-batch-04-karabiner-98k")
        self.assertEqual(set(batch["entity_ids"]), ENTITY_IDS)
        self.assertEqual(batch["relationship_ids"], [RELATIONSHIP_ID])

    def test_entities_are_source_checked_with_technical_profiles(self):
        for entity_id in ENTITY_IDS:
            entity = self.entity_map[entity_id]
            self.assertEqual(entity.provenance.get("review_status"), "source_checked")
            self.assertGreaterEqual(len(entity.provenance.get("sources", [])), 2)
            self.assertGreaterEqual(len(entity.technical.get("claims", [])), 5)
            self.assertEqual(entity.relationships, [])

    def test_relation_is_independent_and_source_checked(self):
        relationship = self.relationship_map[RELATIONSHIP_ID]
        self.assertEqual(relationship.predicate, "uses_ammunition")
        self.assertEqual(relationship.source_id, "ckb:weapon:firearm:karabiner_98k")
        self.assertEqual(relationship.target_id, "ckb:ammunition:cartridge:8x57_is")
        self.assertEqual(relationship.provenance.get("review_status"), "source_checked")
        self.assertGreaterEqual(len(relationship.provenance.get("sources", [])), 2)

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        payload = build_technical_comparison([self.entity_map[entity_id] for entity_id in ENTITY_IDS])
        self.assertEqual(payload["summary"]["profile_entity_count"], 2)
        self.assertEqual(payload["summary"]["claim_count"], 13)
        self.assertEqual(payload["summary"]["unsupported_numeric_count"], 0)

    def test_ammunition_profile_excludes_loading_recipe_fields(self):
        forbidden = {"propellant_charge", "primer_specification", "loading_recipe", "manufacturing_tolerance", "attack_instruction"}
        fields = {claim.get("field") for claim in self.entity_map["ckb:ammunition:cartridge:8x57_is"].technical["claims"]}
        self.assertTrue(fields.isdisjoint(forbidden))

if __name__ == "__main__":
    unittest.main()
