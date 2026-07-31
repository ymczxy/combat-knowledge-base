from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ckb.export import load_profile
from ckb.godot_bundle import build_godot_runtime_bundle, write_godot_runtime_artifacts
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.runtime_contract import validate_runtime_contract


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "data" / "curated" / "destory"
EXPECTED_ENTITY_IDS = [
    "ckb:system:air_defense:patriot",
    "ckb:component:sensor:patriot_an_mpq_65",
    "ckb:weapon:missile:patriot_pac_3_interceptor",
    "ckb:material:reinforced_concrete",
]
EXPECTED_RELATIONSHIP_IDS = [
    "rel:v1_6_4_batch_01:patriot:armed_with:pac_3",
    "rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65",
]
FORBIDDEN_BALANCE_FIELDS = {
    "damage",
    "penetration",
    "explosion",
    "hardness",
    "integrity",
    "impulse",
    "hit_points",
}


class DestoryGameBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")

    def _build(self, profile_name: str):
        profile = load_profile(PROFILE_ROOT / profile_name)
        bundle, errors = build_godot_runtime_bundle(
            self.entities,
            profile,
            project_root=ROOT,
            relationships=self.relationships,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(bundle)
        return profile, bundle

    def test_both_upgrade_releases_have_the_same_game_contract(self):
        cases = [
            (
                "game_build_profile_v1.json",
                "destory-game-ckb-runtime-v1",
                "ckb_destory_game_runtime_v1.ckb",
            ),
            (
                "game_build_profile.json",
                "destory-game-ckb-runtime-v2",
                "ckb_destory_game_runtime_v2.ckb",
            ),
        ]
        for profile_name, bundle_id, filename in cases:
            with self.subTest(profile=profile_name):
                profile, bundle = self._build(profile_name)
                manifest = bundle["manifest"]
                self.assertEqual(manifest["bundle_id"], bundle_id)
                self.assertEqual(
                    profile["godot_runtime_bundle"]["output_filename"],
                    filename,
                )
                self.assertEqual(
                    [row["id"] for row in bundle["entities"]],
                    EXPECTED_ENTITY_IDS,
                )
                self.assertEqual(
                    [row["id"] for row in bundle["relationships"]],
                    EXPECTED_RELATIONSHIP_IDS,
                )
                self.assertEqual(manifest["entity_count"], 4)
                self.assertEqual(manifest["relationship_assertion_count"], 2)
                self.assertEqual(manifest["technical_claim_count"], 16)
                self.assertEqual(manifest["source_ref_count"], 8)
                self.assertIs(manifest["boundaries"]["contains_game_balance"], False)

    def test_game_bundle_excludes_balance_fields_and_resolves_claim_sources(self):
        _, bundle = self._build("game_build_profile.json")
        source_refs = {row["ref"] for row in bundle["source_table"]}
        resolved_claim_count = 0
        for entity in bundle["entities"]:
            for claim in entity.get("technical_claims", []):
                field_name = claim["field"].lower()
                self.assertFalse(
                    any(token in field_name for token in FORBIDDEN_BALANCE_FIELDS),
                    field_name,
                )
                self.assertTrue(claim["source_refs"])
                self.assertTrue(set(claim["source_refs"]).issubset(source_refs))
                resolved_claim_count += 1
        self.assertEqual(resolved_claim_count, 16)

    def test_both_releases_write_locked_contract_valid_artifacts(self):
        for profile_name in ("game_build_profile_v1.json", "game_build_profile.json"):
            with self.subTest(profile=profile_name), TemporaryDirectory() as directory:
                profile, bundle = self._build(profile_name)
                bundle_path, lock_path, _ = write_godot_runtime_artifacts(
                    bundle,
                    profile,
                    Path(directory),
                )
                summary, errors = validate_runtime_contract(bundle_path, lock_path)
                self.assertEqual(errors, [])
                self.assertEqual(summary["entity_count"], 4)
                self.assertEqual(summary["relationship_assertion_count"], 2)
                self.assertEqual(summary["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
