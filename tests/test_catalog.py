import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.catalog import load_catalog, validate_catalog
from ckb.export import load_profile, select_entities
from ckb.model import load_entities
from ckb.sources import load_source_registry, validate_source_registry

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_catalog_has_expected_scope(self):
        items = load_catalog(ROOT / "data" / "catalog")
        self.assertEqual(len(items), 502)
        self.assertEqual(validate_catalog(items), [])

    def test_sources_validate(self):
        rows = load_source_registry(ROOT / "sources" / "registry.json")
        self.assertGreaterEqual(len(rows), 9)
        self.assertEqual(validate_source_registry(rows), [])

    def test_destory_profile_can_build_research_bundle(self):
        entities = load_entities(ROOT / "data" / "canonical")
        profile = load_profile(ROOT / "data" / "curated" / "destory" / "build_profile.json")
        selected = select_entities(entities, profile, allow_unverified=True)
        self.assertGreaterEqual(len(selected), 10)


if __name__ == "__main__": unittest.main()
