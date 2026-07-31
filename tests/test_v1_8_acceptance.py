from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ckb.catalog import load_catalog
from ckb.graph import load_relationships
from ckb.model import load_entities
from ckb.site import build_site_docs


ROOT = Path(__file__).resolve().parents[1]


class V18AcceptanceTests(unittest.TestCase):
    def test_site_query_graph_and_evidence_contract_is_complete(self) -> None:
        entities = load_entities(ROOT / "data" / "canonical")
        relationships = load_relationships(ROOT / "data" / "relationships")
        catalog = load_catalog(ROOT / "data" / "catalog")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "site"
            build_site_docs(entities, catalog, ROOT, output, relationships)
            payload = json.loads(
                (output / "query-index.json").read_text(encoding="utf-8")
            )

            self.assertEqual(payload["schema_version"], "1.1")
            self.assertEqual(payload["contract"]["name"], "ckb.local.query-index")
            self.assertEqual(
                set(payload["contract"]["filter_fields"]),
                {
                    "text",
                    "entity_type",
                    "domain",
                    "class",
                    "subclass",
                    "era",
                    "tag",
                    "review_status",
                    "technical_field",
                    "minimum_sources",
                    "has_technical",
                    "predicate",
                    "direction",
                },
            )
            self.assertEqual(
                payload["contract"]["evidence_chain"],
                ["fact", "assertions", "sources"],
            )
            self.assertTrue(all(row.get("fact_id") for row in payload["relationships"]))
            self.assertTrue(all(row.get("assertions") for row in payload["facts"]))
            self.assertTrue(all(row.get("sources") for row in payload["facts"]))

            for name in (
                "timeline",
                "map",
                "lineage",
                "battle_equipment",
                "industry_chain",
            ):
                self.assertTrue((output / "visualizations" / f"{name}.json").is_file())
                self.assertTrue((output / "visualizations" / f"{name}.md").is_file())

            script = (
                output / "assets" / "javascripts" / "ckb-explorer.js"
            ).read_text(encoding="utf-8")
            for marker in (
                "data-filter",
                "data-graph",
                "dataset.relationshipId",
                "renderRelationshipEvidence",
                "makeGraphNode",
                "fact?.assertions",
            ):
                self.assertIn(marker, script)

            patriot = (
                output / "entities" / "ckb__system__air_defense__patriot.md"
            ).read_text(encoding="utf-8")
            self.assertIn("## 实体关系", patriot)
            self.assertIn("关系断言与证据", patriot)
            self.assertIn("uses_sensor", patriot)
            self.assertIn("us_army_pac3", patriot)


if __name__ == "__main__":
    unittest.main()
