import unittest

from ckb.assertions import aggregate_assertions, canonical_fact_key
from ckb.graph import Relationship
from ckb.predicates import PredicateRegistry


class AssertionGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.registry = PredicateRegistry.from_dict({
            "registry_version": "test",
            "predicates": [
                {
                    "name": "predecessor_of",
                    "labels": {"en": "predecessor of", "zh": "前身"},
                    "description": {"en": "Earlier design.", "zh": "更早设计。"},
                    "inverse": "successor_of",
                },
                {
                    "name": "successor_of",
                    "labels": {"en": "successor of", "zh": "后继"},
                    "description": {"en": "Later design.", "zh": "更晚设计。"},
                    "inverse": "predecessor_of",
                },
            ],
        })

    @staticmethod
    def relation(
        rel_id: str,
        source: str,
        predicate: str,
        target: str,
        *,
        source_id: str = "source_a",
        url: str = "https://example.test/a",
        polarity: str = "affirmed",
    ) -> Relationship:
        return Relationship.from_dict({
            "id": rel_id,
            "source_id": source,
            "predicate": predicate,
            "target_id": target,
            "confidence": 0.8,
            "qualifiers": {"polarity": polarity},
            "provenance": {
                "review_status": "unverified",
                "sources": [{"source_id": source_id, "url": url}],
            },
        })

    def test_inverse_assertions_share_one_canonical_fact(self):
        forward = self.relation("rel:a:b", "ckb:a", "predecessor_of", "ckb:b")
        reverse = self.relation("rel:b:a", "ckb:b", "successor_of", "ckb:a")

        self.assertEqual(
            canonical_fact_key(forward, self.registry),
            canonical_fact_key(reverse, self.registry),
        )
        report = aggregate_assertions([forward, reverse], self.registry)
        self.assertEqual(len(report.facts), 1)
        self.assertEqual(report.facts[0].duplicate_assertion_count, 1)

    def test_sources_are_deduplicated_and_promotion_is_only_suggested(self):
        first = self.relation("rel:a:b:1", "ckb:a", "predecessor_of", "ckb:b")
        repeated = self.relation("rel:a:b:2", "ckb:a", "predecessor_of", "ckb:b")
        independent = self.relation(
            "rel:a:b:3",
            "ckb:a",
            "predecessor_of",
            "ckb:b",
            source_id="source_b",
            url="https://example.test/b",
        )

        fact = aggregate_assertions([first, repeated, independent], self.registry).facts[0]
        self.assertEqual(len(fact.sources), 2)
        self.assertEqual(fact.asserted_review_status, "unverified")
        self.assertEqual(fact.suggested_review_status, "cross_checked")
        self.assertTrue(fact.to_dict()["promotion_recommended"])

    def test_affirmed_and_denied_assertions_create_conflict(self):
        affirmed = self.relation("rel:a:b:yes", "ckb:a", "predecessor_of", "ckb:b")
        denied = self.relation(
            "rel:a:b:no",
            "ckb:a",
            "predecessor_of",
            "ckb:b",
            polarity="denied",
        )

        report = aggregate_assertions([affirmed, denied], self.registry)
        self.assertEqual(len(report.conflicts), 1)
        self.assertTrue(report.facts[0].conflict)
        self.assertEqual(report.facts[0].suggested_review_status, "unverified")


if __name__ == "__main__":
    unittest.main()
