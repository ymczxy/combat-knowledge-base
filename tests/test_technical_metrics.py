import copy
import unittest
from pathlib import Path

from ckb.model import load_entities
from ckb.technical_metrics import (
    build_derived_metrics,
    load_metric_specs,
    render_derived_metrics_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "data" / "derived" / "technical_metrics_v1_6_0_batch_08.json"
EXPECTED_METRIC_IDS = {
    "metric:v1_6_0:m1a2:power_to_mass",
    "metric:v1_6_0:challenger_2:baseline_power_to_mass",
    "metric:v1_6_0:challenger_2:add_on_armour_power_to_mass",
    "metric:v1_6_0:leclerc:authorised_mass_range_power_to_mass",
    "metric:v1_6_0:type_10:power_to_mass",
}


class DerivedTechnicalMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.specification = load_metric_specs(SPECS)
        cls.payload = build_derived_metrics(cls.entities, cls.specification)
        cls.row_map = {row["metric_id"]: row for row in cls.payload["rows"]}

    def test_batch_08_builds_all_explicit_metrics_without_errors(self):
        summary = self.payload["summary"]
        self.assertEqual(summary["specification_count"], 5)
        self.assertEqual(summary["derived_metric_count"], 5)
        self.assertEqual(summary["entity_count"], 4)
        self.assertEqual(summary["error_count"], 0, self.payload["errors"])
        self.assertEqual(set(self.row_map), EXPECTED_METRIC_IDS)

    def test_scalar_power_to_mass_results_match_normalized_inputs(self):
        expected = {
            "metric:v1_6_0:m1a2:power_to_mass": 17.614144,
            "metric:v1_6_0:challenger_2:baseline_power_to_mass": 14.317438,
            "metric:v1_6_0:challenger_2:add_on_armour_power_to_mass": 11.931198,
            "metric:v1_6_0:type_10:power_to_mass": 20.059057,
        }
        for metric_id, value in expected.items():
            row = self.row_map[metric_id]
            self.assertEqual(row["unit"], "kW/t")
            self.assertAlmostEqual(row["value"], value, places=6, msg=metric_id)

    def test_mass_range_produces_ascending_metric_interval(self):
        row = self.row_map[
            "metric:v1_6_0:leclerc:authorised_mass_range_power_to_mass"
        ]
        self.assertEqual(row["value"], [17.511875, 19.700859])
        self.assertEqual(row["inputs"]["mass"]["normalized"]["value"], [56, 63])
        self.assertEqual(
            row["qualifiers"]["output_interpretation"],
            "ascending power-to-mass interval",
        )

    def test_each_metric_retains_formula_inputs_sources_and_boundaries(self):
        for row in self.payload["rows"]:
            self.assertEqual(row["formula"], "engine_power_kW / mass_t")
            self.assertEqual(row["derivation_status"], "derived_from_normalized_public_technical_claims")
            self.assertIs(row["not_source_fact"], True)
            self.assertIs(row["not_game_balance"], True)
            self.assertTrue(row["source_urls"], row["metric_id"])
            for role in ("power", "mass"):
                selected = row["inputs"][role]
                self.assertIsInstance(selected["claim_index"], int)
                self.assertTrue(selected["field"])
                self.assertIsInstance(selected["original"], dict)
                self.assertIsInstance(selected["normalized"], dict)
                self.assertTrue(selected["source_urls"])

    def test_challenger_configurations_remain_separate_metrics(self):
        baseline = self.row_map[
            "metric:v1_6_0:challenger_2:baseline_power_to_mass"
        ]
        armoured = self.row_map[
            "metric:v1_6_0:challenger_2:add_on_armour_power_to_mass"
        ]
        self.assertEqual(baseline["inputs"]["power"]["claim_index"], 7)
        self.assertEqual(armoured["inputs"]["power"]["claim_index"], 7)
        self.assertEqual(baseline["inputs"]["mass"]["claim_index"], 1)
        self.assertEqual(armoured["inputs"]["mass"]["claim_index"], 2)
        self.assertGreater(baseline["value"], armoured["value"])

    def test_claim_index_or_expected_field_drift_fails_instead_of_reselecting(self):
        changed = copy.deepcopy(self.specification)
        changed["metrics"][0]["inputs"]["mass"] = {
            "claim_index": 2,
            "expected_field": "combat_mass",
        }
        payload = build_derived_metrics(self.entities, changed)
        self.assertEqual(payload["summary"]["derived_metric_count"], 4)
        self.assertEqual(payload["summary"]["error_count"], 1)
        self.assertIn("expected field combat_mass", payload["errors"][0])
        self.assertIn("found main_gun_caliber", payload["errors"][0])

    def test_unknown_formula_is_rejected(self):
        changed = copy.deepcopy(self.specification)
        changed["metrics"][0]["formula"] = "guess_vehicle_performance"
        payload = build_derived_metrics(self.entities, changed)
        self.assertEqual(payload["summary"]["derived_metric_count"], 4)
        self.assertTrue(any("unsupported formula" in error for error in payload["errors"]))

    def test_markdown_explains_non_fact_and_non_balance_boundary(self):
        markdown = render_derived_metrics_markdown(self.payload)
        self.assertIn("# 装甲车辆派生指标", markdown)
        self.assertIn("不是来源原文，也不是游戏平衡值", markdown)
        self.assertIn("claim 3", markdown)
        self.assertIn("质量区间输出功重比区间", markdown)
        self.assertIn("../entities/ckb__platform__ground__type_10_tank.md", markdown)


if __name__ == "__main__":
    unittest.main()
