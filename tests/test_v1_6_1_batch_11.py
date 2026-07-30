import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ckb.export import load_profile
from ckb.godot_bundle import build_godot_runtime_bundle, write_godot_runtime_artifacts
from ckb.model import load_entities
from ckb.runtime_contract import validate_runtime_contract

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "data" / "curated" / "destory" / "small_arms_build_profile.json"
EXPECTED = [
    "ckb:weapon:firearm:m2_browning",
    "ckb:ammunition:cartridge:12_7x99",
    "ckb:weapon:firearm:thompson_m1a1",
    "ckb:component:magazine:thompson_wartime_box",
    "ckb:weapon:family:thompson_submachine_gun",
]


class SmallArmsBatch11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.profile = load_profile(PROFILE)
        cls.bundle, cls.errors = build_godot_runtime_bundle(cls.entities, cls.profile, project_root=ROOT)

    def test_small_arms_bundle_is_explicit_and_valid(self):
        self.assertEqual(self.errors, [])
        self.assertIsNotNone(self.bundle)
        self.assertEqual([row["id"] for row in self.bundle["entities"]], EXPECTED)
        self.assertEqual(self.bundle["manifest"]["profile_id"], "destory-small-arms")
        self.assertEqual(self.bundle["manifest"]["derived_metric_count"], 0)
        self.assertEqual(self.bundle["manifest"]["boundaries"]["contains_game_balance"], False)

    def test_weapon_and_ammunition_are_queryable(self):
        rows = {row["id"]: row for row in self.bundle["entities"]}
        self.assertIn("ckb:weapon:firearm:m2_browning", rows)
        self.assertIn("ckb:ammunition:cartridge:12_7x99", rows)
        self.assertGreaterEqual(len(rows["ckb:weapon:firearm:m2_browning"]["technical_claims"]), 5)
        self.assertGreaterEqual(len(rows["ckb:ammunition:cartridge:12_7x99"]["technical_claims"]), 5)

    def test_small_arms_bundle_lock_passes_contract(self):
        with TemporaryDirectory() as directory:
            bundle_path, lock_path, _ = write_godot_runtime_artifacts(self.bundle, self.profile, Path(directory))
            summary, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertEqual(errors, [])
            self.assertEqual(summary["entity_count"], 5)
            self.assertGreater(summary["technical_claim_count"], 0)


if __name__ == "__main__":
    unittest.main()
