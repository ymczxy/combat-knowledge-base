import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
M2_ID = "ckb:weapon:firearm:m2_browning"
AMMO_ID = "ckb:ammunition:cartridge:12_7x99"
REL_ID = "rel:v1_6_1_batch_08:m2_browning:uses_ammunition:12_7x99"


class SmallArmsBatch08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_1_small_arms_batch_08.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_1_small_arms_batch_08.json").read_text())

    def test_both_entities_are_source_checked_and_have_profiles(self):
        for entity_id in (M2_ID, AMMO_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)
            self.assertEqual(entity.gameplay, {"status": "draft"})

    def test_relationship_is_independent_and_explicit(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], M2_ID)
        self.assertEqual(relation["target_id"], AMMO_ID)
        self.assertEqual(relation["predicate"], "uses_ammunition")
        self.assertEqual(relation["provenance"]["review_status"], "source_checked")
        self.assertEqual(self.batch["entity_ids"], [M2_ID, AMMO_ID])
        self.assertEqual(self.entities[M2_ID].relationships, [])
        self.assertEqual(self.entities[AMMO_ID].relationships, [])

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        for entity_id in (M2_ID, AMMO_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])

    def test_safety_boundary(self):
        forbidden = {"propellant_charge", "primer_specification", "loading_recipe", "manufacturing_tolerance", "attack_instruction", "damage", "penetration"}
        for entity_id in (M2_ID, AMMO_ID):
            fields = {claim.get("field") for claim in self.entities[entity_id].technical["claims"]}
            self.assertTrue(fields.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
