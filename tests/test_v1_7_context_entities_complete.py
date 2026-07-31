from __future__ import annotations

import unittest
from pathlib import Path

from ckb.graph import load_relationships
from ckb.model import load_entities


ROOT = Path(__file__).resolve().parents[1]


class CompleteContextEntityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.by_id = {entity.id: entity for entity in cls.entities}

    def test_all_v17_context_entity_kinds_are_present(self) -> None:
        self.assertTrue({"country", "organization", "unit", "conflict", "person", "facility", "place"}.issubset({e.entity_type for e in self.entities}))

    def test_context_graph_connects_manufacturer_person_facility_unit_and_conflict(self) -> None:
        relation_keys = {(row.source_id, row.predicate, row.target_id) for row in self.relationships}
        self.assertIn(("ckb:organization:manufacturer:chrysler_defense", "produces", "ckb:platform:ground:m1_abrams"), relation_keys)
        self.assertIn(("ckb:person:designer:joseph_gavin", "designed", "ckb:platform:ground:m1_abrams"), relation_keys)
        self.assertIn(("ckb:facility:arsenal:detroit_arsenal", "located_in", "ckb:place:facility:detroit"), relation_keys)
        self.assertIn(("ckb:unit:military:us_1st_infantry_division", "participated_in", "ckb:battle:normandy:d_day"), relation_keys)
        self.assertIn(("ckb:battle:normandy:d_day", "part_of", "ckb:conflict:world_war_ii"), relation_keys)

    def test_facility_and_place_have_coordinates_for_map_output(self) -> None:
        for entity_id in ("ckb:facility:arsenal:detroit_arsenal", "ckb:place:facility:detroit"):
            location = self.by_id[entity_id].raw["location"]
            self.assertIn("latitude", location)
            self.assertIn("longitude", location)


if __name__ == "__main__":
    unittest.main()
