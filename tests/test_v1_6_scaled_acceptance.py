from pathlib import Path
import unittest

from ckb.graph import load_relationships
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]


class V16ScaledAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = {
            entity.id: entity
            for entity in load_entities(ROOT / "data" / "canonical")
        }
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.relation_keys = {
            (row.source_id, row.predicate, row.target_id)
            for row in cls.relationships
        }

    def assert_source_checked_profile(
        self,
        entity_id: str,
        *,
        minimum_sources: int = 2,
        minimum_claims: int = 3,
    ):
        entity = self.entities[entity_id]
        self.assertEqual(entity.provenance["review_status"], "source_checked", entity_id)
        self.assertGreaterEqual(
            len(entity.provenance.get("sources", [])),
            minimum_sources,
            entity_id,
        )
        self.assertGreaterEqual(
            len((entity.technical or {}).get("claims", [])),
            minimum_claims,
            entity_id,
        )

    def test_v1_6_2_has_three_aircraft_engine_sensor_weapon_slices(self):
        profile_ids = [
            "ckb:platform:air:spitfire_mk_i",
            "ckb:component:engine:rolls_royce_merlin_ii",
            "ckb:platform:air:f_16c_fighting_falcon",
            "ckb:component:engine:pratt_whitney_f100_pw_220",
            "ckb:platform:air:f_15_eagle_family",
            "ckb:platform:air:f_15e_strike_eagle",
            "ckb:component:sensor:an_apg_82_v1",
            "ckb:weapon:missile:aim_120_amraam",
        ]
        for entity_id in profile_ids:
            with self.subTest(entity_id=entity_id):
                self.assert_source_checked_profile(entity_id, minimum_claims=5)

        expected_relations = {
            (
                "ckb:platform:air:spitfire_mk_i",
                "uses_engine",
                "ckb:component:engine:rolls_royce_merlin_ii",
            ),
            (
                "ckb:platform:air:f_16c_fighting_falcon",
                "uses_engine",
                "ckb:component:engine:pratt_whitney_f100_pw_220",
            ),
            (
                "ckb:platform:air:f_15e_strike_eagle",
                "variant_of",
                "ckb:platform:air:f_15_eagle_family",
            ),
            (
                "ckb:platform:air:f_15e_strike_eagle",
                "uses_engine",
                "ckb:component:engine:pratt_whitney_f100_pw_220",
            ),
            (
                "ckb:platform:air:f_15e_strike_eagle",
                "uses_sensor",
                "ckb:component:sensor:an_apg_82_v1",
            ),
            (
                "ckb:platform:air:f_15e_strike_eagle",
                "armed_with",
                "ckb:weapon:missile:aim_120_amraam",
            ),
        }
        self.assertTrue(expected_relations.issubset(self.relation_keys))

    def test_v1_6_3_has_three_classes_and_vessel_service_system_graphs(self):
        class_ids = {
            "ckb:platform:naval:arleigh_burke_class",
            "ckb:platform:naval:type_45_daring_class",
            "ckb:platform:naval:virginia_class",
        }
        vessel_ids = {
            "ckb:platform:naval:hms_daring_d32",
            "ckb:platform:naval:uss_virginia_ssn_774",
        }
        engine_ids = {
            "ckb:component:engine:ge_lm2500_marine",
            "ckb:component:engine:rolls_royce_wr_21",
            "ckb:component:engine:virginia_class_nuclear_propulsion",
        }
        sensor_ids = {
            "ckb:component:sensor:an_spy_1d",
            "ckb:component:sensor:sampson_radar",
            "ckb:component:sensor:an_bps_16_v4",
        }
        weapon_ids = {
            "ckb:weapon:naval:mk_41_vls",
            "ckb:weapon:naval:sea_viper",
            "ckb:weapon:missile:tomahawk_tlam",
        }
        for entity_id in class_ids | vessel_ids | engine_ids | sensor_ids | weapon_ids:
            with self.subTest(entity_id=entity_id):
                self.assert_source_checked_profile(entity_id)

        self.assertIn(
            (
                "ckb:platform:naval:hms_daring_d32",
                "member_of_class",
                "ckb:platform:naval:type_45_daring_class",
            ),
            self.relation_keys,
        )
        self.assertIn(
            (
                "ckb:platform:naval:uss_virginia_ssn_774",
                "operated_by",
                "ckb:organization:military:united_states_navy",
            ),
            self.relation_keys,
        )

    def test_v1_6_4_has_scaled_artillery_missile_air_defense_and_sensor_sets(self):
        artillery_ids = {
            "ckb:weapon:artillery:stokes_mortar",
            "ckb:weapon:artillery:m777a2_howitzer",
            "ckb:platform:ground:m109a7_paladin",
        }
        air_defense_ids = {
            "ckb:system:air_defense:patriot",
            "ckb:system:air_defense:iron_dome",
            "ckb:system:air_defense:nasams",
        }
        missile_ids = {
            "ckb:weapon:missile:patriot_pac_3_interceptor",
            "ckb:weapon:missile:fgm_148_javelin",
            "ckb:weapon:missile:tamir_interceptor",
            "ckb:weapon:missile:aim_120_amraam",
        }
        sensor_ids = {
            "ckb:component:sensor:patriot_an_mpq_65",
            "ckb:component:sensor:javelin_command_launch_unit",
            "ckb:component:sensor:elm_2084_mmr",
            "ckb:component:sensor:an_mpq_64_sentinel",
        }
        for entity_id in artillery_ids | air_defense_ids | missile_ids | sensor_ids:
            with self.subTest(entity_id=entity_id):
                self.assert_source_checked_profile(entity_id)

        for system_id in (
            "ckb:system:air_defense:patriot",
            "ckb:system:air_defense:iron_dome",
            "ckb:system:air_defense:nasams",
        ):
            predicates = {
                predicate
                for source_id, predicate, _ in self.relation_keys
                if source_id == system_id
            }
            self.assertIn("uses_sensor", predicates, system_id)
            self.assertIn("armed_with", predicates, system_id)


if __name__ == "__main__":
    unittest.main()
