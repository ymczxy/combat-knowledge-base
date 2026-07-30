import unittest

from ckb.assertions import aggregate_assertions
from ckb.fact_lifecycle import (
    FactDecisionLedger,
    apply_fact_decisions,
    build_fact_snapshot,
)
from ckb.graph import Relationship
from ckb.predicates import PredicateRegistry


class FactLifecycleTests(unittest.TestCase):
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
    def relation(rel_id: str, polarity: str = "affirmed") -> Relationship:
        return Relationship.from_dict({
            "id": rel_id,
            "source_id": "ckb:a",
            "predicate": "predecessor_of",
            "target_id": "ckb:b",
            "confidence": 0.8,
            "qualifiers": {"polarity": polarity},
            "provenance": {
                "review_status": "source_checked",
                "sources": [{"source_id": rel_id, "url": f"https://example.test/{rel_id}"}],
            },
        })

    def conflicted_report(self):
        return aggregate_assertions(
            [self.relation("rel:yes"), self.relation("rel:no", "denied")],
            self.registry,
        )

    def test_valid_conflict_history_can_be_applied(self):
        report = self.conflicted_report()
        ledger = FactDecisionLedger.from_dict({
            "ledger_version": "1.0",
            "decisions": [
                {
                    "id": "decision:mark_disputed",
                    "fact_id": "fact:a:predecessor_of:b",
                    "from_status": "proposed",
                    "to_status": "disputed",
                    "decided_by": "reviewer_a",
                    "decided_at": "2026-07-30T00:00:00Z",
                    "reason": "The source assertions disagree.",
                    "assertion_ids": ["rel:yes", "rel:no"],
                },
                {
                    "id": "decision:accept_fact",
                    "fact_id": "fact:a:predecessor_of:b",
                    "from_status": "disputed",
                    "to_status": "accepted",
                    "decided_by": "reviewer_b",
                    "decided_at": "2026-07-30T01:00:00Z",
                    "reason": "The affirmative assertion is supported after review.",
                    "assertion_ids": ["rel:yes", "rel:no"],
                },
            ],
        })

        self.assertEqual(ledger.validate(report), [])
        apply_fact_decisions(report, ledger)
        fact = report.facts[0]
        self.assertEqual(fact.lifecycle_status, "accepted")
        self.assertEqual(fact.current_decision["id"], "decision:accept_fact")
        self.assertEqual(len(fact.decision_history), 2)

    def test_invalid_transition_and_unknown_assertion_are_rejected(self):
        report = aggregate_assertions([self.relation("rel:yes")], self.registry)
        ledger = FactDecisionLedger.from_dict({
            "decisions": [{
                "id": "decision:bad",
                "fact_id": "fact:a:predecessor_of:b",
                "from_status": "accepted",
                "to_status": "deprecated",
                "decided_by": "reviewer",
                "decided_at": "2026-07-30T00:00:00Z",
                "reason": "Invalid test decision.",
                "assertion_ids": ["rel:missing"],
            }],
        })

        errors = ledger.validate(report)
        self.assertTrue(any("does not match current status" in error for error in errors))
        self.assertTrue(any("does not belong" in error for error in errors))

    def test_invalid_timestamp_is_reported_without_crashing(self):
        report = aggregate_assertions([self.relation("rel:yes")], self.registry)
        ledger = FactDecisionLedger.from_dict({
            "decisions": [{
                "id": "decision:bad_time",
                "fact_id": "fact:a:predecessor_of:b",
                "from_status": "proposed",
                "to_status": "accepted",
                "decided_by": "reviewer",
                "decided_at": "not-a-time",
                "reason": "Invalid timestamp test.",
                "assertion_ids": ["rel:yes"],
            }],
        })

        errors = ledger.validate(report)
        self.assertTrue(any("ISO 8601 timestamp" in error for error in errors))

    def test_conflicted_fact_must_enter_disputed_first(self):
        report = self.conflicted_report()
        ledger = FactDecisionLedger.from_dict({
            "decisions": [{
                "id": "decision:skip_disputed",
                "fact_id": "fact:a:predecessor_of:b",
                "from_status": "proposed",
                "to_status": "accepted",
                "decided_by": "reviewer",
                "decided_at": "2026-07-30T00:00:00Z",
                "reason": "Attempted direct resolution.",
                "assertion_ids": ["rel:yes", "rel:no"],
            }],
        })

        errors = ledger.validate(report)
        self.assertTrue(any("must enter disputed" in error for error in errors))

    def test_conflict_resolution_requires_multiple_assertions(self):
        report = self.conflicted_report()
        ledger = FactDecisionLedger.from_dict({
            "decisions": [
                {
                    "id": "decision:dispute",
                    "fact_id": "fact:a:predecessor_of:b",
                    "from_status": "proposed",
                    "to_status": "disputed",
                    "decided_by": "reviewer",
                    "decided_at": "2026-07-30T00:00:00Z",
                    "reason": "Conflict detected.",
                    "assertion_ids": ["rel:yes", "rel:no"],
                },
                {
                    "id": "decision:resolve_badly",
                    "fact_id": "fact:a:predecessor_of:b",
                    "from_status": "disputed",
                    "to_status": "accepted",
                    "decided_by": "reviewer",
                    "decided_at": "2026-07-30T01:00:00Z",
                    "reason": "Insufficiently supported resolution.",
                    "assertion_ids": ["rel:yes"],
                },
            ],
        })

        errors = ledger.validate(report)
        self.assertTrue(any("requires at least two cited assertions" in error for error in errors))

    def test_fact_snapshot_is_deterministic(self):
        first_report = aggregate_assertions([self.relation("rel:yes")], self.registry)
        second_report = aggregate_assertions([self.relation("rel:yes")], self.registry)
        ledger = FactDecisionLedger.from_dict({
            "decisions": [{
                "id": "decision:accept",
                "fact_id": "fact:a:predecessor_of:b",
                "from_status": "proposed",
                "to_status": "accepted",
                "decided_by": "reviewer",
                "decided_at": "2026-07-30T00:00:00Z",
                "reason": "Source reviewed.",
                "assertion_ids": ["rel:yes"],
            }],
        })

        apply_fact_decisions(first_report, ledger)
        apply_fact_decisions(second_report, ledger)
        first = build_fact_snapshot(first_report, ledger)
        second = build_fact_snapshot(second_report, ledger)
        self.assertEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
