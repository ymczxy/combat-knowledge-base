from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ckb.export import load_profile
from ckb.godot_bundle import build_godot_runtime_bundle, write_godot_runtime_artifacts
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.runtime_contract import validate_runtime_contract


ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = ROOT / "data" / "curated" / "destory"

DOMAIN_CASES = {
    "aviation_build_profile.json": {
        "profile_id": "destory-aviation",
        "entity_count": 9,
        "relationship_count": 7,
        "required_relationships": {
            "rel:v1_6_2_batch_01:spitfire_mk_i:uses_engine:merlin_ii",
            "rel:v1_6_2_release:spitfire_mk_i:uses_ammunition:303_british",
            "rel:v1_6_2_batch_02:f_16c:uses_engine:f100_pw_220",
            "rel:v1_6_2_batch_03:f_15e:variant_of:f_15_family",
            "rel:v1_6_2_batch_03:f_15e:uses_sensor:apg_82",
            "rel:v1_6_2_batch_03:f_15e:armed_with:aim_120",
        },
    },
    "naval_build_profile.json": {
        "profile_id": "destory-naval",
        "entity_count": 20,
        "relationship_count": 17,
        "required_relationships": {
            "rel:v1_6_3_release:arleigh_burke:armed_with:mk_45_mod_4",
            "rel:v1_6_3_release:mk_45_mod_4:uses_ammunition:5_inch_62",
            "rel:v1_6_3_batch_02:daring:member_of_class:type_45",
            "rel:v1_6_3_batch_02:daring:operated_by:royal_navy",
            "rel:v1_6_3_batch_02:virginia:uses_engine:nuclear_propulsion",
            "rel:v1_6_3_release:virginia:uses_sensor:an_bqq_10",
            "rel:v1_6_3_release:virginia:armed_with:mk_48_adcap",
        },
    },
    "integrated_systems_build_profile.json": {
        "profile_id": "destory-integrated-systems",
        "entity_count": 16,
        "relationship_count": 10,
        "required_relationships": {
            "rel:v1_6_4_release:m777a2:uses_ammunition:m795",
            "rel:v1_6_4_release:m109a7:uses_ammunition:m795",
            "rel:v1_6_4_release:stokes:uses_ammunition:3_inch_bomb",
            "rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65",
            "rel:v1_6_4_batch_01:patriot:armed_with:pac_3",
            "rel:v1_6_4_batch_02:iron_dome:uses_sensor:elm_2084",
            "rel:v1_6_4_batch_02:iron_dome:armed_with:tamir",
            "rel:v1_6_4_batch_02:nasams:uses_sensor:sentinel",
            "rel:v1_6_4_batch_02:nasams:armed_with:aim_120",
        },
    },
}


class V16FullDomainClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.relationship_map = {row.id: row for row in cls.relationships}

    def _build(self, profile_name: str):
        profile = load_profile(PROFILE_ROOT / profile_name)
        bundle, errors = build_godot_runtime_bundle(
            self.entities,
            profile,
            project_root=ROOT,
            relationships=self.relationships,
        )
        self.assertEqual(errors, [])
        self.assertIsNotNone(bundle)
        return profile, bundle

    def test_each_planned_v16_domain_has_a_locked_runtime_contract(self):
        for profile_name, expected in DOMAIN_CASES.items():
            with self.subTest(profile=profile_name), TemporaryDirectory() as directory:
                profile, bundle = self._build(profile_name)
                manifest = bundle["manifest"]
                self.assertEqual(manifest["profile_id"], expected["profile_id"])
                self.assertEqual(manifest["entity_count"], expected["entity_count"])
                self.assertEqual(
                    manifest["relationship_assertion_count"],
                    expected["relationship_count"],
                )
                actual_relationships = {row["id"] for row in bundle["relationships"]}
                self.assertTrue(
                    expected["required_relationships"] <= actual_relationships
                )
                self.assertIs(manifest["boundaries"]["contains_game_balance"], False)

                bundle_path, lock_path, _ = write_godot_runtime_artifacts(
                    bundle,
                    profile,
                    Path(directory),
                )
                summary, errors = validate_runtime_contract(bundle_path, lock_path)
                self.assertEqual(errors, [])
                self.assertEqual(summary["entity_count"], expected["entity_count"])
                self.assertEqual(
                    summary["relationship_assertion_count"],
                    expected["relationship_count"],
                )

    def test_closure_relationships_are_independent_and_double_sourced(self):
        required = set().union(
            *(case["required_relationships"] for case in DOMAIN_CASES.values())
        )
        for relationship_id in required:
            with self.subTest(relationship_id=relationship_id):
                relationship = self.relationship_map[relationship_id]
                self.assertEqual(
                    relationship.provenance.get("review_status"),
                    "source_checked",
                )
                source_keys = {
                    (source.get("source_id"), source.get("url"))
                    for source in relationship.provenance.get("sources", [])
                }
                self.assertGreaterEqual(len(source_keys), 2)

    def test_no_caliber_only_compatibility_or_embedded_relationships(self):
        closure_ids = {
            "rel:v1_6_2_release:spitfire_mk_i:uses_ammunition:303_british",
            "rel:v1_6_3_release:mk_45_mod_4:uses_ammunition:5_inch_62",
            "rel:v1_6_4_release:m777a2:uses_ammunition:m795",
            "rel:v1_6_4_release:m109a7:uses_ammunition:m795",
            "rel:v1_6_4_release:stokes:uses_ammunition:3_inch_bomb",
        }
        for relationship_id in closure_ids:
            self.assertIs(
                self.relationship_map[relationship_id].qualifiers.get(
                    "not_inferred_from_caliber_alone"
                ),
                True,
            )
        self.assertTrue(all(entity.relationships == [] for entity in self.entities))


if __name__ == "__main__":
    unittest.main()
