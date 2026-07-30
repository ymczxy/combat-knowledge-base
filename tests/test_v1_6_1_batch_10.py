import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.predicates import load_predicate_registry

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "ckb:weapon:firearm:thompson_m1a1"
FAMILY_ID = "ckb:weapon:family:thompson_submachine_gun"
REL_ID = "rel:v1_6_1_batch_10:thompson_m1a1:variant_of:thompson_family"


class SmallArmsBatch10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_1_small_arms_batch_10.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_1_small_arms_batch_10.json").read_text())
        cls.registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    def test_family_is_source_checked_and_profiled(self):
        family = self.entities[FAMILY_ID]
        self.assertEqual(family.entity_type, "weapon")
        self.assertEqual(family.classification["subclass"], "SubmachineGunFamily")
        self.assertEqual(family.provenance["review_status"], "source_checked")
        self.assertGreaterEqual(len(family.provenance["sources"]), 2)
        self.assertGreaterEqual(len(family.technical["claims"]), 5)

    def test_variant_predicate_has_explicit_endpoint_constraints(self):
        predicate = self.registry.get("variant_of")
        self.assertEqual(predicate.source_entity_types, ("weapon", "platform", "system", "component"))
        self.assertEqual(predicate.target_entity_types, ("weapon", "platform", "system", "component"))
        self.assertFalse(predicate.symmetric)
        self.assertFalse(predicate.transitive)
        self.assertEqual(self.registry.inverse_of("variant_of"), "has_variant")

    def test_model_to_family_assertion_preserves_boundary(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], MODEL_ID)
        self.assertEqual(relation["target_id"], FAMILY_ID)
        self.assertEqual(relation["predicate"], "variant_of")
        self.assertIn("named model is a variant", relation["qualifiers"]["scope"])
        self.assertEqual(self.batch["entity_ids"], [FAMILY_ID])

    def test_family_has_no_embedded_relationships(self):
        self.assertEqual(self.entities[FAMILY_ID].relationships, [])


if __name__ == "__main__":
    unittest.main()
