import unittest
from pathlib import Path

from ckb.content_audit import load_content_batches
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ENTITY_IDS = {
    "ckb:platform:ground:m1_abrams",
    "ckb:platform:ground:challenger_2",
    "ckb:platform:ground:leclerc_tank",
    "ckb:platform:ground:type_10_tank",
}


class Batch05ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.batches = load_content_batches(ROOT / "data" / "content_batches")

    def test_batch_registers_exact_profile_entities(self):
        matching = [
            batch
            for batch in self.batches
            if batch.get("batch_id") == "v1.6.0-armored-vehicles-batch-05-profiles"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(set(matching[0].get("entity_ids", [])), PROFILE_ENTITY_IDS)
        self.assertEqual(
            matching[0].get("quality_targets", {}).get(
                "minimum_technical_claims_per_entity"
            ),
            6,
        )
        self.assertIs(
            matching[0].get("quality_targets", {}).get("require_experience_profile"),
            True,
        )

    def test_profile_entities_have_traceable_technical_claims(self):
        entity_map = {entity.id: entity for entity in self.entities}
        self.assertEqual(set(entity_map) & PROFILE_ENTITY_IDS, PROFILE_ENTITY_IDS)
        total_claims = 0
        for entity_id in PROFILE_ENTITY_IDS:
            entity = entity_map[entity_id]
            profile = entity.technical
            self.assertEqual(profile.get("profile_version"), "1.0", entity_id)
            self.assertTrue(profile.get("profile_scope"), entity_id)
            claims = profile.get("claims", [])
            self.assertGreaterEqual(len(claims), 6, entity_id)
            total_claims += len(claims)
            for claim in claims:
                self.assertTrue(claim.get("field"), entity_id)
                self.assertIsNotNone(claim.get("value"), entity_id)
                self.assertTrue(claim.get("unit"), entity_id)
                self.assertIsInstance(claim.get("qualifiers"), dict, entity_id)
                self.assertTrue(claim.get("source_urls"), entity_id)
        self.assertEqual(total_claims, 40)

    def test_experience_profiles_are_explicit_derivatives_not_balance(self):
        entity_map = {entity.id: entity for entity in self.entities}
        for entity_id in PROFILE_ENTITY_IDS:
            profile = entity_map[entity_id].experience_profile
            self.assertEqual(profile.get("profile_version"), "1.0", entity_id)
            self.assertEqual(
                profile.get("derivation_status"),
                "derived_from_public_technical_facts",
                entity_id,
            )
            self.assertTrue(profile.get("basis_fields"), entity_id)
            self.assertTrue(profile.get("cues"), entity_id)
            self.assertIs(profile.get("not_game_balance"), True, entity_id)
            for value in profile.get("dimensions", {}).values():
                self.assertIsInstance(value, (int, float), entity_id)
                self.assertGreaterEqual(value, 0, entity_id)
                self.assertLessEqual(value, 1, entity_id)

    def test_technical_profiles_preserve_configuration_differences(self):
        entity_map = {entity.id: entity for entity in self.entities}
        challenger_claims = entity_map[
            "ckb:platform:ground:challenger_2"
        ].technical["claims"]
        mass_fields = {
            claim["field"]
            for claim in challenger_claims
            if claim["field"] in {"baseline_mass", "combat_ready_mass"}
        }
        self.assertEqual(mass_fields, {"baseline_mass", "combat_ready_mass"})

        abrams_claims = entity_map["ckb:platform:ground:m1_abrams"].technical["claims"]
        self.assertTrue(
            any(claim.get("qualifiers", {}).get("configuration") for claim in abrams_claims)
        )


if __name__ == "__main__":
    unittest.main()
