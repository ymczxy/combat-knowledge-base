import unittest
from pathlib import Path

from ckb.model import Entity, load_entities
from ckb.technical import (
    build_technical_comparison,
    normalize_claim,
    normalize_claim_value,
    render_technical_comparison_markdown,
    technical_normalization_errors,
)


ROOT = Path(__file__).resolve().parents[1]
ARMORED_PROFILE_ENTITY_IDS = {
    "ckb:platform:ground:m1_abrams",
    "ckb:platform:ground:challenger_2",
    "ckb:platform:ground:leclerc_tank",
    "ckb:platform:ground:type_10_tank",
    "ckb:platform:ground:m4_sherman",
    "ckb:platform:ground:t_34_model_1940",
    "ckb:platform:ground:panther_tank",
    "ckb:platform:ground:type_59_tank",
}
SMALL_ARMS_PROFILE_ENTITY_IDS = {
    "ckb:weapon:firearm:akm",
    "ckb:ammunition:cartridge:7_62x39",
    "ckb:weapon:firearm:sa80_a2_individual_weapon",
    "ckb:ammunition:cartridge:5_56x45_nato",
    "ckb:weapon:firearm:m1_garand",
    "ckb:ammunition:cartridge:30_06_springfield",
    "ckb:weapon:firearm:lee_enfield_no4_mk1",
    "ckb:ammunition:cartridge:303_british",
    "ckb:weapon:firearm:karabiner_98k",
    "ckb:ammunition:cartridge:8x57_is",
    "ckb:weapon:firearm:ppsh_41",
    "ckb:ammunition:cartridge:7_62x25_tokarev",
    "ckb:weapon:firearm:thompson_m1a1",
    "ckb:ammunition:cartridge:45_auto",
    "ckb:weapon:firearm:mg42",
    "ckb:weapon:firearm:m2_browning",
    "ckb:ammunition:cartridge:12_7x99",
    "ckb:component:magazine:thompson_wartime_box",
    "ckb:weapon:family:thompson_submachine_gun",
}
PROFILE_ENTITY_IDS = ARMORED_PROFILE_ENTITY_IDS | SMALL_ARMS_PROFILE_ENTITY_IDS
PROFILE_ENTITY_IDS |= {
    "ckb:platform:air:spitfire_mk_i",
    "ckb:component:engine:rolls_royce_merlin_ii",
    "ckb:platform:air:f_16c_fighting_falcon",
    "ckb:component:engine:pratt_whitney_f100_pw_220",
}


def entity_with_claim(claim: dict) -> Entity:
    return Entity.from_dict({
        "id": "ckb:test:technical",
        "entity_type": "platform",
        "identity": {
            "canonical_name_en": "Technical test",
            "canonical_name_zh": "技术测试",
            "aliases": [],
        },
        "classification": {
            "domain": "Platform",
            "class": "GroundVehicle",
            "subclass": "Tank",
            "eras": ["CONTEMPORARY"],
            "tags": ["test"],
        },
        "relationships": [],
        "technical": {
            "profile_version": "1.0",
            "profile_scope": "test",
            "claims": [claim],
        },
        "experience_profile": None,
        "gameplay": {"status": "draft"},
        "provenance": {
            "review_status": "unverified",
            "sources": [{"source_id": "test", "url": "https://example.test"}],
        },
        "rights": {"rights_status": "deferred"},
    })


class TechnicalNormalizationTests(unittest.TestCase):
    def test_mass_speed_range_and_power_units_convert_deterministically(self):
        self.assertEqual(normalize_claim_value("combat_mass", 70, "short_ton"), (63.502932, "t"))
        self.assertEqual(normalize_claim_value("maximum_speed", 42, "mph"), (67.592448, "km/h"))
        self.assertEqual(normalize_claim_value("operational_range", 256, "mi"), (411.992064, "km"))
        self.assertEqual(normalize_claim_value("engine_power", 1500, "hp"), (1118.549807, "kW"))
        self.assertEqual(normalize_claim_value("engine_power", 1200, "PS"), (882.5985, "kW"))

    def test_range_values_preserve_both_endpoints(self):
        value, unit = normalize_claim_value("mass_range", [56, 63], "t")
        self.assertEqual(value, [56, 63])
        self.assertEqual(unit, "t")

    def test_rate_units_use_explicit_rounds_per_minute_target(self):
        self.assertEqual(
            normalize_claim_value("sustained_combat_rate", 4, "rounds_per_minute"),
            (4, "rounds/min"),
        )

    def test_descriptive_claims_are_retained_but_not_ranked(self):
        entity = entity_with_claim({
            "field": "loading_method",
            "value": "autoloader",
            "unit": "categorical",
            "qualifiers": {},
            "source_urls": ["https://example.test/loading"],
        })
        row = normalize_claim(entity, entity.technical["claims"][0], 0)
        self.assertEqual(row["comparison_status"], "descriptive")
        self.assertIsNone(row["normalized"])
        self.assertEqual(row["original"]["value"], "autoloader")

    def test_unknown_numeric_unit_is_reported_not_guessed(self):
        entity = entity_with_claim({
            "field": "engine_power",
            "value": 100,
            "unit": "mystery_power",
            "qualifiers": {},
            "source_urls": ["https://example.test/power"],
        })
        errors = technical_normalization_errors(entity)
        self.assertEqual(len(errors), 1)
        self.assertIn("unsupported source unit mystery_power", errors[0])

    def test_comparison_preserves_original_qualifiers_and_sources(self):
        claim = {
            "field": "maximum_speed",
            "value": 42,
            "unit": "mph",
            "qualifiers": {"configuration": "test variant", "surface": "road"},
            "source_urls": ["https://example.test/speed"],
        }
        entity = entity_with_claim(claim)
        payload = build_technical_comparison([entity])
        row = payload["rows"][0]
        self.assertEqual(row["original"], {"value": 42, "unit": "mph"})
        self.assertEqual(row["normalized"], {"value": 67.592448, "unit": "km/h"})
        self.assertEqual(row["qualifiers"], claim["qualifiers"])
        self.assertEqual(row["source_urls"], claim["source_urls"])


class RepositoryTechnicalComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.payload = build_technical_comparison(cls.entities)

    def test_current_profiles_are_fully_normalizable(self):
        summary = self.payload["summary"]
        self.assertEqual(summary["profile_entity_count"], 31)
        self.assertEqual(summary["claim_count"], 213)
        self.assertEqual(summary["numeric_claim_count"], 94)
        self.assertEqual(summary["normalized_numeric_claim_count"], 94)
        self.assertEqual(summary["descriptive_claim_count"], 119)
        self.assertEqual(
            summary["unsupported_numeric_count"],
            0,
            self.payload["unsupported_numeric_claims"],
        )

    def test_expected_profile_entities_are_present(self):
        actual = {row["entity_id"] for row in self.payload["rows"]}
        self.assertEqual(actual, PROFILE_ENTITY_IDS)

    def test_multiple_configurations_remain_multiple_rows(self):
        rows = [
            row
            for row in self.payload["rows"]
            if row["entity_id"] == "ckb:platform:ground:m4_sherman"
            and row["field"] == "maximum_speed"
        ]
        self.assertEqual(len(rows), 2)
        configurations = {row["qualifiers"].get("configuration") for row in rows}
        self.assertEqual(
            configurations,
            {"M4A2E8 Sherman", "M4A4 Sherman VC Firefly"},
        )

    def test_field_and_entity_filters_are_explicit(self):
        payload = build_technical_comparison(
            self.entities,
            fields=["engine_power"],
            entity_ids=["ckb:platform:ground:m1_abrams"],
        )
        self.assertTrue(payload["rows"])
        self.assertEqual({row["field"] for row in payload["rows"]}, {"engine_power"})
        self.assertEqual(
            {row["entity_id"] for row in payload["rows"]},
            {"ckb:platform:ground:m1_abrams"},
        )

    def test_markdown_contains_comparison_boundary_and_entity_links(self):
        markdown = render_technical_comparison_markdown(self.entities)
        self.assertIn("# 技术参数比较", markdown)
        self.assertIn("原始声明", markdown)
        self.assertIn("配置限定", markdown)
        self.assertIn("不会从多个改型中自行选择一个代表值", markdown)
        self.assertIn("../entities/ckb__platform__ground__m1_abrams.md", markdown)


if __name__ == "__main__":
    unittest.main()
