import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT_ID = "ckb:platform:air:f_16c_fighting_falcon"
ENGINE_ID = "ckb:component:engine:pratt_whitney_f100_pw_220"
REL_ID = "rel:v1_6_2_batch_02:f_16c:uses_engine:f100_pw_220"


class AviationBatch02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_2_aviation_batch_02.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_2_aviation_batch_02.json").read_text())

    def test_entities_are_source_checked_and_have_profiles(self):
        for entity_id in (AIRCRAFT_ID, ENGINE_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)

    def test_engine_relation_is_scoped_and_independent(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], AIRCRAFT_ID)
        self.assertEqual(relation["target_id"], ENGINE_ID)
        self.assertTrue(relation["qualifiers"]["configuration_specific"])
        self.assertEqual(relation["provenance"]["review_status"], "source_checked")
        self.assertEqual(self.batch["entity_ids"], [AIRCRAFT_ID, ENGINE_ID])

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        for entity_id in (AIRCRAFT_ID, ENGINE_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])


if __name__ == "__main__":
    unittest.main()
