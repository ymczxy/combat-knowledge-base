import json
import unittest
from pathlib import Path

from ckb.content_audit import load_content_batches
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.technical import build_technical_comparison


ROOT = Path(__file__).resolve().parents[1]
BATCH_ID = "v1.6.1-small-arms-and-ammunition-batch-01"
ENTITY_IDS = {
    "ckb:weapon:firearm:akm",
    "ckb:ammunition:cartridge:7_62x39",
    "ckb:weapon:firearm:sa80_a2_individual_weapon",
    "ckb:ammunition:cartridge:5_56x45_nato",
}
RELATIONSHIP_IDS = {
    "rel:v1_6_0_batch_04:akm:uses_ammunition:7_62x39",
    "rel:v1_6_1_batch_01:sa80_a2_iw:uses_ammunition:5_56x45_nato",
}


class SmallArmsBatch01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.batches = load_content_batches(ROOT / "data" / "content_batches")
        cls.entity_map = {entity.id: entity for entity in cls.entities}
        cls.relationship_map = {
            relationship.id: relationship for relationship in cls.relationships
        }

    def test_batch_registers_exact_vertical_slice(self):
        matching = [batch for batch in self.batches if batch.get("batch_id") == BATCH_ID]
        self.assertEqual(len(matching), 1)
        batch = matching[0]
        self.assertEqual(batch.get("version"), "1.6.1")
        self.assertEqual(batch.get("status"), "source_checked")
        self.assertEqual(set(batch.get("entity_ids", [])), ENTITY_IDS)
        self.assertEqual(set(batch.get("relationship_ids", [])), RELATIONSHIP_IDS)

    def test_entities_are_unique_source_checked_and_relation_free(self):
        self.assertEqual(set(self.entity_map) & ENTITY_IDS, ENTITY_IDS)
        for entity_id in ENTITY_IDS:
            entity = self.entity_map[entity_id]
            self.assertEqual(entity.provenance.get("review_status"), "source_checked")
            self.assertGreaterEqual(len(entity.provenance.get("sources", [])), 1)
            self.assertEqual(entity.relationships, [])

    def test_weapon_ammunition_relations_are_independent_and_checked(self):
        self.assertEqual(set(self.relationship_map) & RELATIONSHIP_IDS, RELATIONSHIP_IDS)
        expected_pairs = {
            (
                "ckb:weapon:firearm:akm",
                "ckb:ammunition:cartridge:7_62x39",
            ),
            (
                "ckb:weapon:firearm:sa80_a2_individual_weapon",
                "ckb:ammunition:cartridge:5_56x45_nato",
            ),
        }
        actual_pairs = set()
        for relationship_id in RELATIONSHIP_IDS:
            relationship = self.relationship_map[relationship_id]
            self.assertEqual(relationship.predicate, "uses_ammunition")
            self.assertEqual(
                relationship.provenance.get("review_status"), "source_checked"
            )
            self.assertGreaterEqual(len(relationship.provenance.get("sources", [])), 1)
            actual_pairs.add((relationship.source_id, relationship.target_id))
        self.assertEqual(actual_pairs, expected_pairs)

    def test_technical_profiles_normalize_without_unsupported_units(self):
        payload = build_technical_comparison(
            self.entities,
            entity_ids=sorted(ENTITY_IDS),
        )
        self.assertEqual(payload["summary"]["profile_entity_count"], 4)
        self.assertEqual(payload["summary"]["claim_count"], 23)
        self.assertEqual(payload["summary"]["numeric_claim_count"], 13)
        self.assertEqual(payload["summary"]["normalized_numeric_claim_count"], 13)
        self.assertEqual(payload["summary"]["descriptive_claim_count"], 10)
        self.assertEqual(payload["summary"]["unsupported_numeric_count"], 0)

    def test_sa80_preserves_published_configuration_qualifiers(self):
        entity = self.entity_map[
            "ckb:weapon:firearm:sa80_a2_individual_weapon"
        ]
        claims = entity.technical.get("claims", [])
        field_map = {claim.get("field"): claim for claim in claims}
        self.assertEqual(field_map["weapon_mass"]["value"], 4.98)
        self.assertEqual(field_map["weapon_mass"]["unit"], "kg")
        self.assertEqual(
            field_map["weapon_mass"]["qualifiers"].get("condition"),
            "loaded magazine and optical sight",
        )
        self.assertEqual(field_map["cyclic_rate"]["value"], [610, 775])
        self.assertEqual(field_map["magazine_capacity"]["value"], 30)

    def test_ammunition_profiles_exclude_loading_recipe_fields(self):
        allowed_fields = {
            "nominal_caliber",
            "case_length",
            "cartridge_designation",
            "cartridge_case_class",
            "standardization_history",
            "published_ammunition_types",
        }
        for entity_id in {
            "ckb:ammunition:cartridge:7_62x39",
            "ckb:ammunition:cartridge:5_56x45_nato",
        }:
            entity = self.entity_map[entity_id]
            fields = {
                claim.get("field") for claim in entity.technical.get("claims", [])
            }
            self.assertTrue(fields <= allowed_fields, entity_id)
            serialized = json.dumps(entity.technical, ensure_ascii=False).casefold()
            for forbidden in ("propellant", "powder charge", "primer specification"):
                self.assertNotIn(forbidden, serialized, entity_id)

    def test_standards_body_source_is_registered(self):
        registry = json.loads(
            (ROOT / "sources" / "registry.json").read_text(encoding="utf-8")
        )
        source_ids = {row.get("source_id") for row in registry}
        self.assertIn("standards_body", source_ids)


if __name__ == "__main__":
    unittest.main()
