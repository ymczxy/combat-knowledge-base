import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ckb.catalog import load_catalog
from ckb.model import load_entities
from ckb.site import build_site_docs


class SiteTests(unittest.TestCase):
    def test_site_generation(self):
        entities = load_entities(ROOT / "data" / "canonical")
        catalog = load_catalog(ROOT / "data" / "catalog")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "site_docs"
            build_site_docs(entities, catalog, ROOT, output)
            self.assertTrue((output / "index.md").exists())
            self.assertTrue((output / "entities" / "index.md").exists())
            self.assertTrue((output / "catalog" / "index.md").exists())
            self.assertEqual(
                len(list((output / "entities").glob("ckb__*.md"))),
                len(entities),
            )
            catalog_index = (output / "catalog" / "index.md").read_text(encoding="utf-8")
            self.assertIn(str(len(catalog)), catalog_index)


if __name__ == "__main__":
    unittest.main()
