import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.adapters import SourceHit
from ckb.catalog import CatalogItem
from ckb.candidates import build_candidates
from ckb.resolution import SearchCache, decide_matches, infer_entity_scope, score_hit, write_resolution_bundle


class ResolutionTests(unittest.TestCase):
    def candidate(self, group="wwii_armored_vehicles", name="T-34"):
        return build_candidates([CatalogItem(group, name, "researching", "P1", "test.csv")])[0]

    def test_exact_context_match_can_auto_accept(self):
        candidate = self.candidate()
        hits = [
            SourceHit("wikidata", "Q1", "T-34", "Soviet medium tank", "https://example/Q1", ("T34",)),
            SourceHit("wikidata", "Q2", "T-34-85", "Soviet medium tank variant", "https://example/Q2"),
        ]
        rows = decide_matches(candidate, hits)
        self.assertEqual(rows[0].external_id, "Q1")
        self.assertEqual(rows[0].decision, "auto_accept")
        self.assertGreaterEqual(rows[0].score, 0.9)

    def test_ambiguous_candidate_never_auto_accepts(self):
        candidate = self.candidate("early_cold_war", "Javelin")
        hit = SourceHit("wikidata", "Q3", "Javelin", "anti-tank missile", "https://example/Q3")
        row = decide_matches(candidate, [hit])[0]
        self.assertEqual(row.decision, "human_review")

    def test_scope_detection(self):
        candidate = self.candidate("contemporary_naval", "Arleigh Burke class")
        hit = SourceHit("wikidata", "Q4", "Arleigh Burke-class destroyer", "class of guided missile destroyers", "https://example/Q4")
        self.assertEqual(infer_entity_scope(candidate.source_name, hit), "class")

    def test_cache_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = SearchCache(Path(tmp))
            hits = [SourceHit("wikidata", "Q1", "T-34", "tank", "https://example/Q1", ("T34",))]
            cache.put("wikidata", "T-34", hits)
            loaded = cache.get("wikidata", "T-34")
            self.assertEqual(loaded, hits)

    def test_resolution_bundle(self):
        candidate = self.candidate()
        hit = SourceHit("wikidata", "Q1", "T-34", "Soviet medium tank", "https://example/Q1")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_resolution_bundle(decide_matches(candidate, [hit]), output)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["decision_count"], 1)
            self.assertTrue((output / "decisions.json").exists())
            self.assertTrue((output / "review_queue.json").exists())


if __name__ == "__main__":
    unittest.main()
