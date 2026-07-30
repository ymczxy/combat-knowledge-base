from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json

from .assertions import AssertionGovernanceReport


FACT_STATUSES = {"proposed", "accepted", "disputed", "rejected", "deprecated"}
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "proposed": {"accepted", "disputed", "rejected"},
    "accepted": {"disputed", "deprecated"},
    "disputed": {"accepted", "rejected", "deprecated"},
    "rejected": {"proposed", "deprecated"},
    "deprecated": {"proposed"},
}
_RESOLUTION_STATUSES = {"accepted", "rejected", "deprecated"}


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


@dataclass(frozen=True, slots=True)
class FactDecision:
    id: str
    fact_id: str
    from_status: str
    to_status: str
    decided_by: str
    decided_at: str
    reason: str
    assertion_ids: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FactDecision":
        return cls(
            id=str(data["id"]),
            fact_id=str(data["fact_id"]),
            from_status=str(data["from_status"]),
            to_status=str(data["to_status"]),
            decided_by=str(data["decided_by"]),
            decided_at=str(data["decided_at"]),
            reason=str(data["reason"]),
            assertion_ids=tuple(str(value) for value in data.get("assertion_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "fact_id": self.fact_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "reason": self.reason,
            "assertion_ids": list(self.assertion_ids),
        }

    def sort_key(self) -> tuple[datetime, str]:
        return (_parse_timestamp(self.decided_at), self.id)


@dataclass(slots=True)
class FactDecisionLedger:
    decisions: list[FactDecision]
    version: str = "1.0"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | list[Mapping[str, Any]]) -> "FactDecisionLedger":
        if isinstance(payload, list):
            rows = payload
            version = "1.0"
        else:
            rows = payload.get("decisions", [])
            version = str(payload.get("ledger_version", "1.0"))
        return cls([FactDecision.from_dict(row) for row in rows], version=version)

    def grouped(self) -> dict[str, list[FactDecision]]:
        grouped: dict[str, list[FactDecision]] = defaultdict(list)
        for decision in self.decisions:
            grouped[decision.fact_id].append(decision)
        return {
            fact_id: sorted(rows, key=lambda row: row.sort_key())
            for fact_id, rows in grouped.items()
        }

    def validate(self, report: AssertionGovernanceReport) -> list[str]:
        errors: list[str] = []
        facts = {fact.id: fact for fact in report.facts}
        seen_ids: set[str] = set()

        for decision in self.decisions:
            prefix = f"decision:{decision.id}"
            if decision.id in seen_ids:
                errors.append(f"{prefix}: duplicate decision id")
            seen_ids.add(decision.id)
            if not decision.id.startswith("decision:"):
                errors.append(f"{prefix}: id must start with decision:")
            if decision.from_status not in FACT_STATUSES:
                errors.append(f"{prefix}: invalid from_status {decision.from_status}")
            if decision.to_status not in FACT_STATUSES:
                errors.append(f"{prefix}: invalid to_status {decision.to_status}")
            if not decision.decided_by.strip():
                errors.append(f"{prefix}: decided_by is required")
            if not decision.reason.strip():
                errors.append(f"{prefix}: reason is required")
            try:
                _parse_timestamp(decision.decided_at)
            except (ValueError, TypeError):
                errors.append(f"{prefix}: decided_at must be an ISO 8601 timestamp with timezone")

            fact = facts.get(decision.fact_id)
            if fact is None:
                errors.append(f"{prefix}: unknown fact {decision.fact_id}")
                continue
            unknown_assertions = sorted(set(decision.assertion_ids) - set(fact.assertion_ids))
            for assertion_id in unknown_assertions:
                errors.append(f"{prefix}: assertion {assertion_id} does not belong to {decision.fact_id}")

        for fact_id, decisions in self.grouped().items():
            fact = facts.get(fact_id)
            if fact is None:
                continue
            current = "proposed"
            for decision in decisions:
                prefix = f"decision:{decision.id}"
                if decision.from_status != current:
                    errors.append(
                        f"{prefix}: from_status {decision.from_status} does not match current status {current}"
                    )
                    current = decision.to_status
                    continue
                allowed = _ALLOWED_TRANSITIONS.get(current, set())
                if decision.to_status not in allowed:
                    errors.append(
                        f"{prefix}: transition {current} -> {decision.to_status} is not allowed"
                    )
                if (
                    fact.conflict
                    and current == "disputed"
                    and decision.to_status in _RESOLUTION_STATUSES
                    and len(set(decision.assertion_ids)) < 2
                ):
                    errors.append(
                        f"{prefix}: resolving a conflicted fact requires at least two cited assertions"
                    )
                current = decision.to_status

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_version": self.version,
            "decision_count": len(self.decisions),
            "decisions": [
                decision.to_dict()
                for decision in sorted(self.decisions, key=lambda row: (row.fact_id, *row.sort_key()))
            ],
        }


def load_fact_decisions(path: Path) -> FactDecisionLedger:
    if not path.exists():
        return FactDecisionLedger([])
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, (dict, list)):
        raise ValueError(f"Fact decision ledger must be an object or array: {path}")
    return FactDecisionLedger.from_dict(payload)


def apply_fact_decisions(
    report: AssertionGovernanceReport,
    ledger: FactDecisionLedger,
) -> AssertionGovernanceReport:
    grouped = ledger.grouped()
    for fact in report.facts:
        decisions = grouped.get(fact.id, [])
        history = [decision.to_dict() for decision in decisions]
        fact.decision_history = history
        fact.current_decision = history[-1] if history else None
        fact.lifecycle_status = decisions[-1].to_status if decisions else "proposed"
        fact.suggested_lifecycle_status = (
            "disputed" if fact.conflict and fact.lifecycle_status == "proposed" else fact.lifecycle_status
        )
    return report


def build_fact_snapshot(
    report: AssertionGovernanceReport,
    ledger: FactDecisionLedger,
) -> dict[str, Any]:
    core = {
        "snapshot_version": "1.0",
        "fact_count": len(report.facts),
        "lifecycle_counts": report.lifecycle_counts,
        "facts": [fact.to_dict() for fact in sorted(report.facts, key=lambda row: row.id)],
        "decision_ledger": ledger.to_dict(),
    }
    canonical = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return {"snapshot_id": f"sha256:{digest}", **core}
