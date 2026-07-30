import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ckb.export import load_profile
from ckb.godot_bundle import build_godot_runtime_bundle, write_godot_runtime_artifacts
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.runtime_contract import validate_runtime_contract


ROOT = Path(__file__).resolve().parents[1]


class GodotRelationshipBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entities = load_entities(ROOT / "data" / "canonical")
        relationships = load_relationships(ROOT / "data" / "relationships")
        profile = load_profile(ROOT / "data" / "curated" / "destory" / "small_arms_build_profile.json")
        cls.profile = profile
        cls.bundle, cls.errors = build_godot_runtime_bundle(
            entities,
            profile,
            project_root=ROOT,
            relationships=relationships,
        )

    def test_selected_independent_relationships_are_in_bundle(self):
        self.assertEqual(self.errors, [])
        self.assertIsNotNone(self.bundle)
        relation_ids = [row["id"] for row in self.bundle["relationships"]]
        self.assertEqual(
            relation_ids,
            [
                "rel:v1_6_1_batch_08:m2_browning:uses_ammunition:12_7x99",
                "rel:v1_6_1_batch_09:thompson_m1a1:accepts_magazine:thompson_wartime_box",
                "rel:v1_6_1_batch_10:thompson_m1a1:variant_of:thompson_family",
            ],
        )
        self.assertEqual(self.bundle["manifest"]["relationship_assertion_count"], 3)

    def test_relationship_lock_and_contract_are_linked(self):
        with TemporaryDirectory() as directory:
            bundle_path, lock_path, _ = write_godot_runtime_artifacts(self.bundle, self.profile, Path(directory))
            summary, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertEqual(errors, [])
            self.assertEqual(summary["relationship_assertion_count"], 3)


if __name__ == "__main__":
    unittest.main()
