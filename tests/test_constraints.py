import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.adapters import SourceHit
from ckb.batch_resolution import apply_constraints, resolve_cached_candidates, write_batch_bundle
from ckb.candidates import build_candidates
from ckb.catalog import CatalogItem
from ckb.constraints import evaluate_constraints
from ckb.resolution import SearchCache


class ConstraintTests(unittest.TestCase):
    def candidate(self, group: str, name: str):
        return build_candidates([CatalogItem(group, name, "researching", "P1", "test.csv")])[0]

    def test_class_context_and_era_are_compatible(self):
        candidate = self.candidate("wwii_armored_vehicles", "T-34")
        hit = SourceHit("wikidata", "Q1", "T-34", "Soviet medium tank introduced in 1940", "https://example.test/Q1")
        result = evaluate_constraints(candidate, hit)
        self.assertTrue(result.compatible)
        self.assertIn("tank", result.matched_terms)
        self.assertIn("era_year_compatible", result.matched_terms)
        self.assertGreater(result.adjustment, 0)

    def test_wrong_entity_type_is_penalized(self):
        candidate = self.candidate("wwii_aircraft", "Spitfire")
        hit = SourceHit("wikidata", "Q2", "Spitfire", "2018 film and soundtrack album", "https://example.test/Q2")
        result = evaluate_constraints(candidate, hit)
        self.assertFalse(result.compatible)
        self.assertIn("film", result.conflicts)
        self.assertLess(result.adjustment, 0)

    def test_constraints_prevent_false_auto_accept(self):
        candidate = self.candidate("wwii_aircraft", "Spitfire")
        hits = [SourceHit("wikidata", "Q2", "Spitfire", "2018 film and soundtrack album", "https://example.test/Q2")]
        rows = apply_constraints(candidate, hits)
        self.assertNotEqual(rows[0].final_decision, "auto_accept")

    def test_cached_batch_reports_missing_and_writes_bundle(self):
        candidate = self.candidate("wwii_armored_vehicles", "T-34")
        hit = SourceHit("wikidata", "Q1", "T-34", "Soviet medium tank introduced in 1940", "https://example.test/Q1")
        missing_candidate = self.candidate("wwii_aircraft", "Spitfire")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = SearchCache(root / "cache")
            cache.put("wikidata", "T-34", [hit], "en")
            decisions, missing = resolve_cached_candidates([candidate, missing_candidate], cache)
            self.assertEqual(len(decisions), 1)
            self.assertEqual(len(missing), 1)
            write_batch_bundle(decisions, missing, root / "output")
            self.assertTrue((root / "output" / "manifest.json").exists())
            self.assertTrue((root / "output" / "missing_cache.json").exists())


if __name__ == "__main__":
    unittest.main()
