import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT_ID = "ckb:platform:air:spitfire_mk_i"
ENGINE_ID = "ckb:component:engine:rolls_royce_merlin_ii"
REL_ID = "rel:v1_6_2_batch_01:spitfire_mk_i:uses_engine:merlin_ii"


class AviationBatch01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_2_aviation_batch_01.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_2_aviation_batch_01.json").read_text())

    def test_entities_are_source_checked_and_have_profiles(self):
        for entity_id in (AIRCRAFT_ID, ENGINE_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)
            self.assertEqual(entity.gameplay, {"status": "draft"})

    def test_engine_relation_is_explicit_and_independent(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], AIRCRAFT_ID)
        self.assertEqual(relation["target_id"], ENGINE_ID)
        self.assertEqual(relation["predicate"], "uses_engine")
        self.assertTrue(relation["qualifiers"]["configuration_specific"])
        self.assertEqual(relation["provenance"]["review_status"], "source_checked")
        self.assertEqual(self.batch["entity_ids"], [AIRCRAFT_ID, ENGINE_ID])
        self.assertEqual(self.entities[AIRCRAFT_ID].relationships, [])
        self.assertEqual(self.entities[ENGINE_ID].relationships, [])

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        for entity_id in (AIRCRAFT_ID, ENGINE_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])

    def test_safety_boundary(self):
        forbidden = {"maintenance_procedure", "construction_instruction", "flight_instruction", "weapon_employment"}
        for entity_id in (AIRCRAFT_ID, ENGINE_ID):
            fields = {claim.get("field") for claim in self.entities[entity_id].technical["claims"]}
            self.assertTrue(fields.isdisjoint(forbidden))
