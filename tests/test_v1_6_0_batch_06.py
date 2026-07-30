import unittest
from pathlib import Path

from ckb.content_audit import load_content_batches
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ENTITY_IDS = {
    "ckb:platform:ground:m4_sherman",
    "ckb:platform:ground:t_34_model_1940",
    "ckb:platform:ground:panther_tank",
    "ckb:platform:ground:type_59_tank",
}


class Batch06HistoricalProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.batches = load_content_batches(ROOT / "data" / "content_batches")
        cls.entity_map = {entity.id: entity for entity in cls.entities}

    def test_batch_registers_historical_profile_entities(self):
        matching = [
            batch
            for batch in self.batches
            if batch.get("batch_id")
            == "v1.6.0-armored-vehicles-batch-06-historical-profiles"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(set(matching[0].get("entity_ids", [])), PROFILE_ENTITY_IDS)

    def test_historical_profiles_have_expected_claim_total(self):
        total_claims = 0
        for entity_id in PROFILE_ENTITY_IDS:
            entity = self.entity_map[entity_id]
            self.assertEqual(entity.provenance.get("review_status"), "source_checked")
            self.assertGreaterEqual(len(entity.provenance.get("sources", [])), 2)
            claims = entity.technical.get("claims", [])
            self.assertGreaterEqual(len(claims), 6, entity_id)
            total_claims += len(claims)
        self.assertEqual(total_claims, 31)

    def test_sherman_preserves_variant_specific_claims(self):
        claims = self.entity_map["ckb:platform:ground:m4_sherman"].technical["claims"]
        configurations = {
            claim.get("qualifiers", {}).get("configuration")
            for claim in claims
            if claim.get("qualifiers", {}).get("configuration")
        }
        self.assertIn("M4A2E8 Sherman", configurations)
        self.assertIn("M4A4 Sherman VC Firefly", configurations)
        speed_claims = [claim for claim in claims if claim.get("field") == "maximum_speed"]
        self.assertEqual(len(speed_claims), 2)
        self.assertNotEqual(speed_claims[0]["value"], speed_claims[1]["value"])

    def test_t34_and_panther_receive_second_sources(self):
        for entity_id in {
            "ckb:platform:ground:t_34_model_1940",
            "ckb:platform:ground:panther_tank",
        }:
            sources = {
                (source.get("source_id"), source.get("url"))
                for source in self.entity_map[entity_id].provenance.get("sources", [])
            }
            self.assertGreaterEqual(len(sources), 2, entity_id)

    def test_panther_classification_is_specific(self):
        panther = self.entity_map["ckb:platform:ground:panther_tank"]
        self.assertEqual(panther.classification.get("subclass"), "MediumTank")
        self.assertIn("german", panther.classification.get("tags", []))
        self.assertIn("medium_tank", panther.classification.get("tags", []))

    def test_all_experience_profiles_are_derived_not_balance(self):
        for entity_id in PROFILE_ENTITY_IDS:
            profile = self.entity_map[entity_id].experience_profile
            self.assertEqual(
                profile.get("derivation_status"),
                "derived_from_public_technical_facts",
                entity_id,
            )
            self.assertIs(profile.get("not_game_balance"), True, entity_id)
            for value in profile.get("dimensions", {}).values():
                self.assertGreaterEqual(value, 0, entity_id)
                self.assertLessEqual(value, 1, entity_id)


if __name__ == "__main__":
    unittest.main()
