import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.temporal import build_temporal_index, normalize_historical_date


ROOT = Path(__file__).resolve().parents[1]


class TemporalNormalizationTests(unittest.TestCase):
    def test_day_precision_is_lossless(self):
        self.assertEqual(
            normalize_historical_date("6 June 1944"),
            {"original": "6 June 1944", "normalized": "1944-06-06", "precision": "day", "status": "normalized"},
        )

    def test_year_precision_does_not_invent_month_precision(self):
        self.assertEqual(normalize_historical_date("1917")["precision"], "year")

    def test_unknown_date_is_explicitly_unparsed(self):
        self.assertEqual(normalize_historical_date("spring 1944")["status"], "unparsed")

    def test_repository_context_dates_are_indexed(self):
        payload = build_temporal_index(load_entities(ROOT / "data" / "canonical"))
        self.assertGreaterEqual(payload["summary"]["date_claim_count"], 4)
        self.assertEqual(payload["summary"]["unparsed_count"], 0)
        row = next(row for row in payload["rows"] if row["entity_id"] == "ckb:battle:normandy:d_day")
        self.assertEqual(row["normalized"], "1944-06-06")


if __name__ == "__main__":
    unittest.main()
