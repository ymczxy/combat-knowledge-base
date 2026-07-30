import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.predicates import load_predicate_registry
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ID = "ckb:system:air_defense:patriot"
MISSILE_ID = "ckb:weapon:missile:patriot_pac_3_interceptor"
RADAR_ID = "ckb:component:sensor:patriot_an_mpq_65"


class AirDefenseBatch01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_4_air_defense_batch_01.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_4_air_defense_batch_01.json").read_text())
        cls.registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    def test_entities_are_source_checked_and_profiled(self):
        for entity_id in (SYSTEM_ID, MISSILE_ID, RADAR_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)

    def test_sensor_predicate_has_component_boundary(self):
        predicate = self.registry.get("uses_sensor")
        self.assertEqual(predicate.source_entity_types, ("weapon", "platform", "system"))
        self.assertEqual(predicate.target_entity_types, ("component",))
        self.assertEqual(self.registry.inverse_of("uses_sensor"), "sensor_used_by")

    def test_system_links_are_explicit_and_independent(self):
        predicates = {(item["source_id"], item["target_id"]): item["predicate"] for item in self.relationships}
        self.assertEqual(predicates[(SYSTEM_ID, RADAR_ID)], "uses_sensor")
        self.assertEqual(predicates[(SYSTEM_ID, MISSILE_ID)], "armed_with")
        self.assertEqual(self.batch["entity_ids"], [SYSTEM_ID, MISSILE_ID, RADAR_ID])
        self.assertEqual(self.entities[SYSTEM_ID].relationships, [])

    def test_profiles_normalize_without_unsupported_numeric_units(self):
        for entity_id in (SYSTEM_ID, MISSILE_ID, RADAR_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])


if __name__ == "__main__":
    unittest.main()
