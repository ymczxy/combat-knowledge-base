import unittest
from pathlib import Path

from ckb.graph import KnowledgeGraph, load_relationships
from ckb.model import load_entities
from ckb.predicates import load_predicate_registry
from ckb.query import related_entities, search_entities


ROOT = Path(__file__).resolve().parents[1]


class QueryFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entities = load_entities(ROOT / "data" / "canonical")
        cls.graph = KnowledgeGraph(
            cls.entities,
            load_relationships(ROOT / "data" / "relationships"),
            predicate_registry=load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json"),
        )

    def test_search_is_explicit_and_deterministic(self):
        rows = search_entities(self.entities, text="Normandy", entity_type="place", limit=10)
        self.assertEqual([row.id for row in rows], ["ckb:place:region:normandy"])
        self.assertEqual([row.id for row in search_entities(self.entities, domain="Component", era="WWII", limit=2)], sorted(row.id for row in search_entities(self.entities, domain="Component", era="WWII", limit=2)))

    def test_search_filters_do_not_infer_relationships(self):
        rows = search_entities(self.entities, text="Patriot", entity_type="system")
        self.assertEqual([row.id for row in rows], ["ckb:system:air_defense:patriot"])

    def test_related_entities_supports_independent_assertions(self):
        related = related_entities(self.graph, "ckb:system:air_defense:patriot", predicate="uses_sensor", direction="out")
        self.assertEqual([row.id for row in related], ["ckb:component:sensor:patriot_an_mpq_65"])

    def test_limit_must_be_positive(self):
        with self.assertRaises(ValueError):
            search_entities(self.entities, limit=0)

    def test_advanced_filters_are_composable_and_exact(self):
        rows = search_entities(
            self.entities,
            entity_class="Manufacturer",
            review_status="source_checked",
            technical_field="industry",
            minimum_sources=2,
            has_technical=True,
            limit=20,
        )
        self.assertGreaterEqual(len(rows), 5)
        self.assertTrue(
            all(row.classification.get("class") == "Manufacturer" for row in rows)
        )
        self.assertTrue(all(len(row.provenance.get("sources", [])) >= 2 for row in rows))

    def test_minimum_sources_must_be_non_negative(self):
        with self.assertRaises(ValueError):
            search_entities(self.entities, minimum_sources=-1)


if __name__ == "__main__":
    unittest.main()
