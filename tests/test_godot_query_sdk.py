import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "examples" / "godot" / "CKBQuery.gd"
SMOKE = ROOT / "examples" / "godot_smoke" / "Smoke.gd"


class GodotQuerySdkTests(unittest.TestCase):
    def test_sdk_exposes_search_and_explicit_configuration_queries(self):
        source = SDK.read_text(encoding="utf-8")
        for signature in (
            "func search(",
            "func get_entity(",
            "func list_configurations(",
            "func get_claims_for_configuration(",
            "func resolve_source_refs(",
            "func related(",
        ):
            self.assertIn(signature, source)

    def test_real_smoke_uses_sdk_search(self):
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn('const QueryScript = preload("res://CKBQuery.gd")', source)
        self.assertIn('query.search("Sherman", "platform", "WWII", 10)', source)


if __name__ == "__main__":
    unittest.main()
