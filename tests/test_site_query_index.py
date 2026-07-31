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


class SiteQueryIndexTests(unittest.TestCase):
    def test_site_contains_relationship_browse_and_machine_index(self) -> None:
        entities = load_entities(ROOT / "data" / "canonical")
        catalog = load_catalog(ROOT / "data" / "catalog")
        relationships = load_relationships(ROOT / "data" / "relationships")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "site"
            build_site_docs(entities, catalog, ROOT, output, relationships)
            index = json.loads((output / "query-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["schema_version"], "1.1")
            self.assertEqual(len(index["entities"]), len(entities))
            self.assertEqual(len(index["relationships"]), len(relationships))
            self.assertEqual(index["contract"]["evidence_chain"], ["fact", "assertions", "sources"])
            self.assertTrue(index["facts"])
            self.assertTrue(all(row["assertions"] for row in index["facts"]))
            self.assertTrue(any(row["predicate"] == "uses_sensor" for row in index["relationships"]))
            self.assertTrue((output / "relationships" / "index.md").exists())
            self.assertTrue((output / "explorer" / "index.md").exists())
            self.assertTrue((output / "assets" / "javascripts" / "ckb-explorer.js").exists())
            self.assertTrue((output / "assets" / "stylesheets" / "ckb-explorer.css").exists())

            patriot_page = (
                output / "entities" / "ckb__system__air_defense__patriot.md"
            ).read_text(encoding="utf-8")
            self.assertIn("rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65", patriot_page)
            self.assertIn("关系断言与证据", patriot_page)


if __name__ == "__main__":
    unittest.main()
