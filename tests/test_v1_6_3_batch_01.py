import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
SHIP_ID = "ckb:platform:naval:arleigh_burke_class"
ENGINE_ID = "ckb:component:engine:ge_lm2500_marine"
REL_ID = "rel:v1_6_3_batch_01:arleigh_burke:uses_engine:lm2500"


class NavalBatch01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_3_naval_batch_01.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_3_naval_batch_01.json").read_text())

    def test_entities_are_source_checked_and_profiled(self):
        for entity_id in (SHIP_ID, ENGINE_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)

    def test_propulsion_relation_is_explicit_and_independent(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], SHIP_ID)
        self.assertEqual(relation["target_id"], ENGINE_ID)
        self.assertEqual(relation["predicate"], "uses_engine")
        self.assertTrue(relation["qualifiers"]["configuration_specific"])
        self.assertEqual(relation["provenance"]["review_status"], "source_checked")
        self.assertEqual(self.batch["entity_ids"], [SHIP_ID, ENGINE_ID])
        self.assertEqual(self.entities[SHIP_ID].relationships, [])
        self.assertEqual(self.entities[ENGINE_ID].relationships, [])

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        for entity_id in (SHIP_ID, ENGINE_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])


if __name__ == "__main__":
    unittest.main()
