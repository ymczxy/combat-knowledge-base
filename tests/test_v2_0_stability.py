import unittest
from pathlib import Path

from ckb.compatibility import CURRENT_RELEASE, check_runtime_compatibility, migration_policy
from ckb.stability_gate import run_stability_gate


ROOT = Path(__file__).resolve().parents[1]


class V20StabilityTests(unittest.TestCase):
    def test_compatibility_contract_is_explicit(self):
        self.assertEqual(CURRENT_RELEASE, "2.0.0")
        self.assertEqual(check_runtime_compatibility({"bundle_format": "ckb.godot.runtime", "format_version": 1, "schema_version": "1.0"}, {"lock_version": 1}), [])
        self.assertTrue(check_runtime_compatibility({"bundle_format": "wrong", "format_version": 9, "schema_version": "9.0"}, {"lock_version": 9}))
        self.assertGreaterEqual(len(migration_policy()["rules"]), 3)

    def test_stability_gate_passes(self):
        summary, errors = run_stability_gate(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(summary["release"], "2.0.0")
        self.assertEqual(summary["temporal"]["unparsed_count"], 0)
        self.assertEqual(summary["query_search_count"], 1)
        self.assertEqual(summary["query_related_count"], 1)
        self.assertEqual(summary["runtime"]["small_arms_build_profile.json"]["relationship_assertion_count"], 3)


if __name__ == "__main__":
    unittest.main()
