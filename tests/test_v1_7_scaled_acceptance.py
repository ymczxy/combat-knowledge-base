from __future__ import annotations

from pathlib import Path
import unittest

from ckb.graph import load_relationships
from ckb.model import Entity, load_entities
from ckb.visualizations import build_visualization_datasets


ROOT = Path(__file__).resolve().parents[1]
EQUIPMENT_TYPES = {"platform", "weapon", "system", "component", "ammunition"}


def _source_count(entity: Entity) -> int:
    return len(
        {
            (str(source.get("source_id", "")), str(source.get("url", "")))
            for source in entity.provenance.get("sources", [])
            if isinstance(source, dict)
        }
    )


def _claim_count(entity: Entity) -> int:
    claims = entity.technical.get("claims", []) if isinstance(entity.technical, dict) else []
    return len(claims) if isinstance(claims, list) else 0


class V17ScaledAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")
        cls.entity_map = {entity.id: entity for entity in cls.entities}
        cls.datasets = build_visualization_datasets(cls.entities, cls.relationships)

    def test_all_nine_context_categories_are_scaled_and_evidence_backed(self) -> None:
        categories = {
            "Place": lambda entity: entity.entity_type == "place",
            "Country": lambda entity: entity.entity_type == "country",
            "Organization": lambda entity: (
                entity.entity_type == "organization"
                and entity.classification.get("class") not in {"Manufacturer", "MilitaryUnit"}
            ),
            "Manufacturer": lambda entity: entity.classification.get("class") == "Manufacturer",
            "MilitaryUnit": lambda entity: entity.classification.get("class") == "MilitaryUnit",
            "Battle": lambda entity: entity.entity_type == "battle",
            "Conflict": lambda entity: entity.entity_type == "conflict",
            "Person": lambda entity: entity.entity_type == "person",
            "Facility": lambda entity: entity.entity_type == "facility",
        }
        for name, predicate in categories.items():
            with self.subTest(category=name):
                accepted = [
                    entity
                    for entity in self.entities
                    if predicate(entity)
                    and entity.provenance.get("review_status") == "source_checked"
                    and _source_count(entity) >= 2
                    and _claim_count(entity) >= 3
                ]
                self.assertGreaterEqual(
                    len(accepted),
                    5,
                    f"{name} requires at least five source-checked, multi-source, profiled entities",
                )

    def test_all_five_v17_outputs_have_scaled_content(self) -> None:
        timeline_equipment_ids = {
            row["entity_id"]
            for row in self.datasets["timeline"]["rows"]
            if self.entity_map[row["entity_id"]].entity_type in EQUIPMENT_TYPES
        }
        self.assertGreaterEqual(len(timeline_equipment_ids), 5)

        battle_equipment_edges = [
            edge
            for edge in self.datasets["battle_equipment"]["edges"]
            if self.entity_map[edge["source_id"]].entity_type in EQUIPMENT_TYPES
            and self.entity_map[edge["target_id"]].entity_type == "battle"
        ]
        self.assertGreaterEqual(len(battle_equipment_edges), 5)
        self.assertGreaterEqual(len({edge["target_id"] for edge in battle_equipment_edges}), 5)

        production_edges = [
            edge
            for edge in self.datasets["industry_chain"]["edges"]
            if edge["predicate"] in {"produces", "produced_by"}
        ]
        self.assertGreaterEqual(len(production_edges), 5)

        factory_locations = self.datasets["factory_location"]["rows"]
        self.assertGreaterEqual(len(factory_locations), 5)
        self.assertTrue(all(row["location"] for row in factory_locations))
        self.assertTrue(all(len(row["source_urls"]) >= 1 for row in factory_locations))

        organization_edges = self.datasets["unit_organization"]["edges"]
        self.assertGreaterEqual(len(organization_edges), 5)
        self.assertGreaterEqual(
            len(
                {
                    edge["source_id"]
                    for edge in organization_edges
                    if self.entity_map[edge["source_id"]].entity_type == "unit"
                }
            ),
            4,
        )


if __name__ == "__main__":
    unittest.main()
