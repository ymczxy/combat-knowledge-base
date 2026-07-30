import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
MG42_ID = "ckb:weapon:firearm:mg42"
AMMO_ID = "ckb:ammunition:cartridge:8x57_is"
REL_ID = "rel:v1_6_1_batch_07:mg42:uses_ammunition:8x57_is"


class SmallArmsBatch07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_1_small_arms_batch_07.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_1_small_arms_batch_07.json").read_text())

    def test_mg42_is_source_checked_with_technical_profile(self):
        entity = self.entities[MG42_ID]
        self.assertEqual(entity.provenance["review_status"], "source_checked")
        self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
        self.assertGreaterEqual(len(entity.technical["claims"]), 5)
        self.assertEqual(entity.gameplay, {"status": "draft"})

    def test_relation_reuses_existing_ammunition_entity(self):
        self.assertIn(AMMO_ID, self.entities)
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], MG42_ID)
        self.assertEqual(relation["target_id"], AMMO_ID)
        self.assertEqual(relation["predicate"], "uses_ammunition")
        self.assertEqual(relation["provenance"]["review_status"], "source_checked")
        self.assertEqual(self.batch["entity_ids"], [MG42_ID])

    def test_profile_normalizes_without_unsupported_numeric_units(self):
        self.assertEqual(technical_normalization_errors(self.entities[MG42_ID]), [])

    def test_ammunition_safety_boundary(self):
        forbidden = {"propellant_charge", "primer_specification", "loading_recipe", "manufacturing_tolerance", "attack_instruction"}
        fields = {claim.get("field") for claim in self.entities[AMMO_ID].technical["claims"]}
        self.assertTrue(fields.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
