import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.catalog import CatalogItem
from ckb.candidates import build_candidates
from ckb.promotion import build_proposals, write_promotion_bundle


class PromotionTests(unittest.TestCase):
    def test_best_decision_becomes_ready_proposal(self):
        candidate = build_candidates([
            CatalogItem("wwii_armored_vehicles", "T-34", "researching", "P1", "x.csv")
        ])[0]
        decisions = [{
            "candidate_id": candidate.candidate_id,
            "external_source": "wikidata",
            "external_id": "Q170142",
            "external_label": "T-34",
            "external_url": "https://www.wikidata.org/wiki/Q170142",
            "adjusted_score": 0.96,
            "final_decision": "auto_accept",
            "suggested_canonical_id": "ckb:platform:groundvehicle:t_34",
        }]
        rows = build_proposals([candidate], decisions)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].promotion_status, "promotion_ready")
        self.assertEqual(rows[0].proposed_id, "ckb:platform:groundvehicle:t_34")

    def test_ambiguous_candidate_stays_in_review(self):
        candidate = build_candidates([
            CatalogItem("early_cold_war", "Example", "researching", "P1", "x.csv")
        ])[0]
        decisions = [{
            "candidate_id": candidate.candidate_id,
            "external_source": "wikidata",
            "external_id": "Q1",
            "external_label": "Example",
            "score": 0.99,
            "decision": "auto_accept",
        }]
        row = build_proposals([candidate], decisions)[0]
        self.assertEqual(row.promotion_status, "review_required")
        self.assertIn("candidate_ambiguity", row.blockers)

    def test_bundle_contains_ready_and_review_queues(self):
        candidate = build_candidates([
            CatalogItem("wwii_aircraft", "Spitfire", "researching", "P1", "x.csv")
        ])[0]
        proposal = build_proposals([candidate], [{
            "candidate_id": candidate.candidate_id,
            "external_source": "wikidata",
            "external_id": "Q2095",
            "external_label": "Supermarine Spitfire",
            "adjusted_score": 0.93,
            "final_decision": "auto_accept",
        }])
        with tempfile.TemporaryDirectory() as tmp:
            write_promotion_bundle(proposal, Path(tmp))
            self.assertTrue((Path(tmp) / "manifest.json").exists())
            self.assertTrue((Path(tmp) / "promotion_ready.json").exists())


if __name__ == "__main__":
    unittest.main()
