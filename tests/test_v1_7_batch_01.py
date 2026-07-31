import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.predicates import load_predicate_registry
from ckb.technical import technical_normalization_errors


ROOT = Path(__file__).resolve().parents[1]
PLACE_ID = "ckb:place:region:normandy"
EVENT_ID = "ckb:event:operation:overlord"
BATTLE_ID = "ckb:battle:normandy:d_day"
ORG_ID = "ckb:organization:military:us_1st_infantry_division"


class ContextBatch01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_7_context_batch_01.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_7_context_batch_01.json").read_text())
        cls.registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    def test_context_entities_are_source_checked_and_profiled(self):
        for entity_id in (PLACE_ID, EVENT_ID, BATTLE_ID, ORG_ID):
            entity = self.entities[entity_id]
            self.assertEqual(entity.provenance["review_status"], "source_checked")
            self.assertGreaterEqual(len(entity.provenance["sources"]), 2)
            self.assertGreaterEqual(len(entity.technical["claims"]), 5)

    def test_endpoint_constraints_are_explicit(self):
        self.assertEqual(self.registry.get("located_in").source_entity_types, ("place", "facility", "organization", "event", "battle"))
        self.assertEqual(self.registry.get("located_in").target_entity_types, ("place",))
        self.assertEqual(self.registry.get("part_of").source_entity_types, ("event", "battle"))
        self.assertEqual(self.registry.get("organized_by").target_entity_types, ("organization",))
        self.assertEqual(self.registry.get("participated_in").source_entity_types, ("platform", "weapon", "system", "organization", "unit"))

    def test_context_graph_preserves_participation_boundary(self):
        relation_map = {(item["source_id"], item["target_id"]): item for item in self.relationships}
        self.assertEqual(relation_map[(EVENT_ID, PLACE_ID)]["predicate"], "located_in")
        self.assertEqual(relation_map[(BATTLE_ID, EVENT_ID)]["predicate"], "part_of")
        self.assertEqual(relation_map[(ORG_ID, BATTLE_ID)]["predicate"], "participated_in")
        rejected = relation_map[(EVENT_ID, ORG_ID)]
        self.assertEqual(rejected["provenance"]["review_status"], "rejected")
        self.assertEqual(rejected["qualifiers"]["status"], "rejected_inference")
        self.assertEqual(self.batch["entity_ids"], [PLACE_ID, EVENT_ID, BATTLE_ID, ORG_ID])

    def test_context_profiles_have_no_unsupported_numeric_units(self):
        for entity_id in (PLACE_ID, EVENT_ID, BATTLE_ID, ORG_ID):
            self.assertEqual(technical_normalization_errors(self.entities[entity_id]), [])


if __name__ == "__main__":
    unittest.main()
