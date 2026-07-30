import json
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.predicates import load_predicate_registry

ROOT = Path(__file__).resolve().parents[1]
WEAPON_ID = "ckb:weapon:firearm:thompson_m1a1"
MAGAZINE_ID = "ckb:component:magazine:thompson_wartime_box"
REL_ID = "rel:v1_6_1_batch_09:thompson_m1a1:accepts_magazine:thompson_wartime_box"


class SmallArmsBatch09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {entity.id: entity for entity in load_entities(ROOT / "data" / "canonical")}
        cls.relationships = json.loads((ROOT / "data" / "relationships" / "v1_6_1_small_arms_batch_09.json").read_text())
        cls.batch = json.loads((ROOT / "data" / "content_batches" / "v1_6_1_small_arms_batch_09.json").read_text())
        cls.registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")

    def test_magazine_is_a_component_with_explicit_profile(self):
        magazine = self.entities[MAGAZINE_ID]
        self.assertEqual(magazine.entity_type, "component")
        self.assertEqual(magazine.classification["domain"], "Component")
        self.assertEqual(magazine.classification["class"], "Magazine")
        self.assertEqual(magazine.provenance["review_status"], "source_checked")
        self.assertGreaterEqual(len(magazine.technical["claims"]), 5)

    def test_directional_accepts_magazine_predicate_is_constrained(self):
        predicate = self.registry.get("accepts_magazine")
        self.assertEqual(predicate.source_entity_types, ("weapon",))
        self.assertEqual(predicate.target_entity_types, ("component",))
        self.assertFalse(predicate.symmetric)
        self.assertFalse(predicate.transitive)
        self.assertEqual(self.registry.inverse_of("accepts_magazine"), "magazine_accepted_by")

    def test_relation_has_explicit_interface_evidence(self):
        relation = next(item for item in self.relationships if item["id"] == REL_ID)
        self.assertEqual(relation["source_id"], WEAPON_ID)
        self.assertEqual(relation["target_id"], MAGAZINE_ID)
        self.assertEqual(relation["predicate"], "accepts_magazine")
        self.assertEqual(relation["qualifiers"]["compatibility_basis"], "explicit box-magazine statement")
        self.assertEqual(self.batch["entity_ids"], [MAGAZINE_ID])

    def test_no_embedded_relationships_or_unsafe_fields(self):
        self.assertEqual(self.entities[MAGAZINE_ID].relationships, [])
        forbidden = {"loading_recipe", "manufacturing_tolerance", "attack_instruction", "damage", "penetration"}
        fields = {claim["field"] for claim in self.entities[MAGAZINE_ID].technical["claims"]}
        self.assertTrue(fields.isdisjoint(forbidden))


if __name__ == "__main__":
    unittest.main()
