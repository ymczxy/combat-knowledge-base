import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ckb.adapters import MediaWikiAdapter, WikidataAdapter
from ckb.importers import load_entity_csv


class ImporterAndAdapterTests(unittest.TestCase):
    def test_csv_import_preserves_source_and_external_ids(self):
        content = (
            "name_en,name_zh,entity_type,domain,class,subclass,eras,aliases,source_id,source_url,tags,external_id_wikidata\n"
            "AKM,AKM突击步枪,weapon,Weapon,Firearm,AssaultRifle,EARLY_COLD_WAR|LATE_COLD_WAR,AKM rifle,wikidata,https://www.wikidata.org/wiki/Q170604,infantry|gas_operated,Q170604\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "import.csv"
            path.write_text(content, encoding="utf-8")
            rows = load_entity_csv(path)
        self.assertEqual(len(rows), 1)
        payload = rows[0].payload
        self.assertEqual(payload["identity"]["canonical_name_zh"], "AKM突击步枪")
        self.assertEqual(payload["classification"]["eras"], ["EARLY_COLD_WAR", "LATE_COLD_WAR"])
        self.assertEqual(payload["external_ids"]["wikidata"], "Q170604")
        self.assertEqual(payload["provenance"]["review_status"], "machine_imported")

    def test_wikidata_parser(self):
        payload = {"search": [{
            "id": "Q170604", "label": "AKM", "description": "assault rifle",
            "concepturi": "https://www.wikidata.org/entity/Q170604", "aliases": ["AKM rifle"]
        }]}
        hits = WikidataAdapter().parse_search(payload)
        self.assertEqual(hits[0].external_id, "Q170604")
        self.assertEqual(hits[0].aliases, ("AKM rifle",))

    def test_mediawiki_parser(self):
        payload = {"query": {"search": [{"pageid": 123, "title": "T-34", "snippet": "tank"}]}}
        hits = MediaWikiAdapter("en").parse_search(payload)
        self.assertEqual(hits[0].external_id, "123")
        self.assertTrue(hits[0].url.endswith("/wiki/T-34"))


if __name__ == "__main__":
    unittest.main()
