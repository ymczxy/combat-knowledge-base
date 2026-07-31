from __future__ import annotations

import unittest
from pathlib import Path

from ckb.graph import KnowledgeGraph, load_relationships
from ckb.model import load_entities
from ckb.predicates import load_predicate_registry
from ckb.query import entity_evidence, fact_evidence


ROOT = Path(__file__).resolve().parents[1]


class QueryEvidenceTests(unittest.TestCase):
    def test_entity_query_returns_raw_assertions_and_sources(self) -> None:
        entities = load_entities(ROOT / "data" / "canonical")
        relationships = load_relationships(ROOT / "data" / "relationships")
        registry = load_predicate_registry(ROOT / "data" / "ontology" / "predicates.json")
        graph = KnowledgeGraph(entities, relationships, predicate_registry=registry)
        payload = entity_evidence(graph, "ckb:system:air_defense:patriot", predicate="uses_sensor", direction="out")
        self.assertEqual(payload["entity"]["id"], "ckb:system:air_defense:patriot")
        self.assertEqual(len(payload["assertions"]), 1)
        self.assertEqual(payload["assertions"][0]["id"], "rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65")
        self.assertTrue(payload["source_urls"])

        report = graph.governance_report()
        fact = next(
            row
            for row in report.facts
            if "rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65"
            in row.assertion_ids
        )
        fact_payload = fact_evidence(graph, fact.id)
        self.assertEqual(fact_payload["fact"]["id"], fact.id)
        self.assertEqual(
            fact_payload["assertions"][0]["id"],
            "rel:v1_6_4_batch_01:patriot:uses_sensor:an_mpq_65",
        )
        self.assertTrue(fact_payload["source_urls"])


if __name__ == "__main__":
    unittest.main()
