import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.catalog import CatalogItem
from ckb.candidates import ambiguity_groups, build_candidates, candidate_id, normalize_name, stable_slug


class CandidateTests(unittest.TestCase):
    def test_normalization_and_slug_are_stable(self):
        self.assertEqual(normalize_name("  T–34  "), "t-34")
        self.assertEqual(stable_slug("T–34"), "t_34")

    def test_candidate_id_uses_group_namespace(self):
        item = CatalogItem("wwii_armored_vehicles", "T-34", "planned", "P1", "x.csv")
        self.assertEqual(candidate_id(item), "ckb:candidate:wwii_armored_vehicles:t_34")

    def test_same_name_across_groups_is_ambiguous_not_duplicate(self):
        rows = build_candidates([
            CatalogItem("ancient_and_medieval_melee", "Javelin", "planned", "P1", "a.csv"),
            CatalogItem("contemporary_missiles_and_air_defense", "Javelin", "planned", "P1", "b.csv"),
        ])
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.resolution_status == "ambiguous" for row in rows))
        self.assertIn("javelin", ambiguity_groups(rows))
        self.assertNotEqual(rows[0].candidate_id, rows[1].candidate_id)

    def test_mixed_group_enters_review_queue(self):
        row = build_candidates([
            CatalogItem("early_cold_war", "Example", "planned", "P2", "x.csv")
        ])[0]
        self.assertEqual(row.resolution_status, "ambiguous")
        self.assertEqual(row.domain, "Mixed")

    def test_candidate_becomes_reviewable_draft(self):
        row = build_candidates([
            CatalogItem("wwii_aircraft", "P-51 Mustang", "planned", "P1", "x.csv")
        ])[0]
        draft = row.to_draft()
        self.assertEqual(draft["entity_type"], "platform")
        self.assertEqual(draft["identity"]["canonical_name_en"], "P-51 Mustang")
        self.assertEqual(draft["classification"]["eras"], ["WWII"])
        self.assertEqual(draft["provenance"]["review_status"], "machine_imported")
        self.assertEqual(draft["provenance"]["resolution"]["status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
