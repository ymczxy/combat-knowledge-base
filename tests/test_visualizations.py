from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.visualizations import build_visualization_datasets, write_visualization_artifacts


ROOT = Path(__file__).resolve().parents[1]


class VisualizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.relationships = load_relationships(ROOT / "data" / "relationships")

    def test_all_roadmap_visualization_datasets_exist(self) -> None:
        datasets = build_visualization_datasets(self.entities, self.relationships)
        self.assertEqual(
            set(datasets),
            {
                "graph",
                "timeline",
                "map",
                "lineage",
                "battle_equipment",
                "industry_chain",
                "factory_location",
                "unit_organization",
            },
        )
        self.assertEqual(len(datasets["graph"]["nodes"]), len(self.entities))
        self.assertEqual(len(datasets["graph"]["edges"]), len(self.relationships))
        self.assertIn("summary", datasets["timeline"])

    def test_visualization_artifacts_are_reproducible_and_site_consumable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            write_visualization_artifacts(self.entities, self.relationships, first)
            write_visualization_artifacts(self.entities, self.relationships, second)
            for name in (
                "graph",
                "timeline",
                "map",
                "lineage",
                "battle_equipment",
                "industry_chain",
                "factory_location",
                "unit_organization",
            ):
                self.assertEqual(
                    (first / f"{name}.json").read_bytes(), (second / f"{name}.json").read_bytes()
                )
                self.assertTrue((first / f"{name}.md").is_file())
            payload = json.loads((first / "graph.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
