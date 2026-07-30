from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from ckb.export import load_profile
from ckb.godot_bundle import (
    build_godot_runtime_bundle,
    validate_godot_runtime_bundle,
    write_godot_runtime_artifacts,
)
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "curated" / "destory" / "build_profile.json"
EXPECTED_ENTITY_IDS = [
    "ckb:platform:ground:m1_abrams",
    "ckb:platform:ground:challenger_2",
    "ckb:platform:ground:leclerc_tank",
    "ckb:platform:ground:type_10_tank",
    "ckb:platform:ground:m4_sherman",
    "ckb:platform:ground:t_34_model_1940",
    "ckb:platform:ground:panther_tank",
    "ckb:platform:ground:type_59_tank",
]


class GodotRuntimeBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.profile = load_profile(PROFILE_PATH)
        cls.bundle, cls.errors = build_godot_runtime_bundle(
            cls.entities,
            cls.profile,
            project_root=ROOT,
        )

    def test_bundle_builds_current_profile_without_errors(self):
        self.assertEqual(self.errors, [])
        self.assertIsNotNone(self.bundle)
        manifest = self.bundle["manifest"]
        self.assertEqual(manifest["bundle_format"], "ckb.godot.runtime")
        self.assertEqual(manifest["profile_id"], "destory")
        self.assertEqual(manifest["entity_count"], 8)
        self.assertEqual(manifest["technical_claim_count"], 71)
        self.assertEqual(manifest["normalized_numeric_claim_count"], 55)
        self.assertEqual(manifest["descriptive_claim_count"], 16)
        self.assertEqual(manifest["derived_metric_count"], 5)
        self.assertEqual(validate_godot_runtime_bundle(self.bundle), [])

    def test_entity_order_is_explicit_and_runtime_rows_are_compact(self):
        entity_ids = [row["id"] for row in self.bundle["entities"]]
        self.assertEqual(entity_ids, EXPECTED_ENTITY_IDS)
        forbidden = {"provenance", "rights", "gameplay", "raw", "relationships"}
        for entity in self.bundle["entities"]:
            self.assertFalse(forbidden & set(entity), entity["id"])
            self.assertIn("technical_claims", entity)
            self.assertIn("configurations", entity)
            for claim in entity["technical_claims"]:
                self.assertNotIn("source_urls", claim)
                self.assertNotIn("original", claim)

    def test_source_urls_are_deduplicated_into_integer_refs(self):
        source_table = self.bundle["source_table"]
        urls = [row["url"] for row in source_table]
        refs = [row["ref"] for row in source_table]
        self.assertEqual(urls, sorted(set(urls)))
        self.assertEqual(refs, list(range(len(source_table))))
        valid_refs = set(refs)
        for entity in self.bundle["entities"]:
            for row in [*entity["technical_claims"], *entity["derived_metrics"]]:
                self.assertTrue(set(row["source_refs"]) <= valid_refs)

    def test_multi_configuration_entities_remain_separate(self):
        entity_map = {row["id"]: row for row in self.bundle["entities"]}
        sherman_labels = {
            row["label"]
            for row in entity_map["ckb:platform:ground:m4_sherman"]["configurations"]
        }
        self.assertIn("M4A2E8 Sherman", sherman_labels)
        self.assertIn("M4A4 Sherman VC Firefly", sherman_labels)

        challenger = entity_map["ckb:platform:ground:challenger_2"]
        metric_labels = {
            row["qualifiers"]["configuration"]
            for row in challenger["derived_metrics"]
        }
        self.assertEqual(metric_labels, {"baseline", "with add-on armour modules"})

    def test_derived_metrics_reference_existing_local_claims(self):
        for entity in self.bundle["entities"]:
            claim_refs = {row["claim_ref"] for row in entity["technical_claims"]}
            for metric in entity["derived_metrics"]:
                self.assertTrue(set(metric["input_claim_refs"]) <= claim_refs)
                self.assertIs(metric["not_source_fact"], True)
                self.assertIs(metric["not_game_balance"], True)

    def test_bundle_and_lock_are_deterministic_and_linked(self):
        with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
            first_bundle, first_lock, first_lock_payload = write_godot_runtime_artifacts(
                self.bundle,
                self.profile,
                Path(first_dir),
            )
            second_bundle, second_lock, second_lock_payload = write_godot_runtime_artifacts(
                self.bundle,
                self.profile,
                Path(second_dir),
            )
            self.assertEqual(first_bundle.read_bytes(), second_bundle.read_bytes())
            self.assertEqual(first_lock.read_bytes(), second_lock.read_bytes())
            self.assertEqual(first_lock_payload, second_lock_payload)
            self.assertEqual(
                first_lock_payload["content_sha256"],
                self.bundle["manifest"]["content_sha256"],
            )
            self.assertEqual(
                first_lock_payload["entity_ids"],
                EXPECTED_ENTITY_IDS,
            )
            bundle_from_disk = json.loads(first_bundle.read_text(encoding="utf-8"))
            self.assertEqual(validate_godot_runtime_bundle(bundle_from_disk), [])

    def test_tampered_payload_is_rejected_by_content_digest(self):
        tampered = deepcopy(self.bundle)
        tampered["entities"][0]["display_name"]["en"] = "tampered"
        errors = validate_godot_runtime_bundle(tampered)
        self.assertIn("manifest.content_sha256 does not match bundle payload", errors)

    def test_unverified_runtime_entity_is_rejected(self):
        profile = deepcopy(self.profile)
        profile["godot_runtime_bundle"]["entity_ids"] = [
            "ckb:platform:ground:t_18"
        ]
        bundle, errors = build_godot_runtime_bundle(
            self.entities,
            profile,
            project_root=ROOT,
        )
        self.assertIsNone(bundle)
        self.assertTrue(any("review_status unverified" in error for error in errors))

    def test_schema_file_is_present(self):
        self.assertTrue((ROOT / "schemas" / "godot_runtime_bundle.schema.json").is_file())


if __name__ == "__main__":
    unittest.main()
