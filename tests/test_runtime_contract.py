from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from ckb.export import load_profile
from ckb.godot_bundle import (
    build_godot_runtime_bundle,
    write_godot_runtime_artifacts,
)
from ckb.model import load_entities
from ckb.runtime_contract import validate_runtime_contract


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "curated" / "destory" / "build_profile.json"
LOADER_PATH = ROOT / "examples" / "godot" / "CKBRuntimeBundle.gd"


class RuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.profile = load_profile(PROFILE_PATH)
        cls.bundle, cls.bundle_errors = build_godot_runtime_bundle(
            cls.entities,
            cls.profile,
            project_root=ROOT,
        )

    def _write_artifacts(self, root: Path):
        self.assertEqual(self.bundle_errors, [])
        self.assertIsNotNone(self.bundle)
        return write_godot_runtime_artifacts(
            self.bundle,
            self.profile,
            root,
        )

    def test_valid_bundle_and_lock_pass_contract(self):
        with TemporaryDirectory() as directory:
            bundle_path, lock_path, _ = self._write_artifacts(Path(directory))
            summary, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertEqual(errors, [])
            self.assertEqual(summary["bundle_format"], "ckb.godot.runtime")
            self.assertEqual(summary["format_version"], 1)
            self.assertEqual(summary["schema_version"], "1.0")
            self.assertEqual(summary["entity_count"], 8)
            self.assertEqual(summary["technical_claim_count"], 71)
            self.assertEqual(summary["derived_metric_count"], 5)
            self.assertEqual(summary["error_count"], 0)

    def test_tampered_bundle_file_fails_file_hash(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle_path, lock_path, _ = self._write_artifacts(root)
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            payload["entities"][0]["display_name"]["en"] = "tampered"
            bundle_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertTrue(
                any("bundle_file_sha256" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("content_sha256" in error for error in errors),
                errors,
            )

    def test_reordered_lock_entity_ids_are_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle_path, lock_path, lock = self._write_artifacts(root)
            lock["entity_ids"] = list(reversed(lock["entity_ids"]))
            lock_path.write_text(
                json.dumps(lock, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertIn(
                "lock.entity_ids does not match the Bundle entity order",
                errors,
            )

    def test_unsupported_format_version_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle_path, lock_path, lock = self._write_artifacts(root)
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            payload["manifest"]["format_version"] = 2
            bundle_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            lock["format_version"] = 2
            lock["bundle_file_sha256"] = "invalid"
            lock["resource_manifest"][0]["sha256"] = "invalid"
            lock_path.write_text(
                json.dumps(lock, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertTrue(
                any("unsupported format_version 2" in error for error in errors),
                errors,
            )

    def test_resource_manifest_path_is_locked(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundle_path, lock_path, lock = self._write_artifacts(root)
            lock["resource_manifest"][0]["path"] = "other.json"
            lock_path.write_text(
                json.dumps(lock, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            _, errors = validate_runtime_contract(bundle_path, lock_path)
            self.assertIn(
                "lock.resource_manifest[0].path does not match Bundle filename",
                errors,
            )

    def test_godot_loader_exposes_only_explicit_configuration_queries(self):
        source = LOADER_PATH.read_text(encoding="utf-8")
        required_fragments = [
            "class_name CKBRuntimeBundle",
            "FileAccess.get_sha256(bundle_path)",
            "JSON.parse_string",
            "func get_claims_for_configuration",
            "func get_metrics_for_configuration",
            "func list_configurations",
            "func resolve_source_refs",
            "SUPPORTED_FORMAT_VERSION: int = 1",
            "SUPPORTED_SCHEMA_VERSION: String = \"1.0\"",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, source)
        self.assertNotIn("select_best_configuration", source)
        self.assertNotIn("auto_select", source)

    def test_batch_10_manifest_is_present(self):
        self.assertTrue(
            (
                ROOT
                / "data"
                / "content_batches"
                / "v1_6_0_armored_batch_10_godot_loader_contract.json"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
