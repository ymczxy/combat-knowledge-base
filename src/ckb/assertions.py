from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from .predicates import PredicateRegistry


_REVIEW_RANK = {
    "planned": 0,
    "unverified": 1,
    "machine_imported": 2,
    "source_checked": 3,
    "cross_checked": 4,
    "expert_reviewed": 5,
    "deprecated": -1,
}


def _source_key(source: dict[str, Any]) -> tuple[str, str]:
    return (str(source.get("source_id", "")), str(source.get("url", "")))


def _polarity(relationship: Any) -> str:
    value = str(relationship.qualifiers.get("polarity", "affirmed")).lower()
    return value if value in {"affirmed", "denied"} else "affirmed"


@dataclass(frozen=True, slots=True)
class FactKey:
    source_id: str
    predicate: str
    target_id: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.source_id, self.predicate, self.target_id)

    def to_dict(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "predicate": self.predicate,
            "target_id": self.target_id,
        }


@dataclass(slots=True)
class CanonicalFact:
    id: str
    key: FactKey
    assertion_ids: list[str]
    sources: list[dict[str, Any]]
    confidence: float
    review_status: str
    polarities: list[str]
    conflict: bool = False
    duplicate_assertion_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            **self.key.to_dict(),
            "assertion_ids": self.assertion_ids,
            "assertion_count": len(self.assertion_ids),
            "duplicate_assertion_count": self.duplicate_assertion_count,
            "sources": self.sources,
            "source_count": len(self.sources),
            "confidence": self.confidence,
            "review_status": self.review_status,
            "polarities": self.polarities,
            "conflict": self.conflict,
        }


@dataclass(slots=True)
class AssertionGovernanceReport:
    facts: list[CanonicalFact] = field(default_factory=list)

    @property
    def duplicate_groups(self) -> list[CanonicalFact]:
        return [fact for fact in self.facts if fact.duplicate_assertion_count > 0]

    @property
    def conflicts(self) -> list[CanonicalFact]:
        return [fact for fact in self.facts if fact.conflict]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_count": len(self.facts),
            "duplicate_group_count": len(self.duplicate_groups),
            "conflict_count": len(self.conflicts),
            "facts": [fact.to_dict() for fact in self.facts],
            "duplicate_groups": [fact.to_dict() for fact in self.duplicate_groups],
            "conflicts": [fact.to_dict() for fact in self.conflicts],
        }


def canonical_fact_key(relationship: Any, registry: PredicateRegistry | None) -> FactKey:
    direct = FactKey(
        source_id=str(relationship.source_id),
        predicate=str(relationship.predicate),
        target_id=str(relationship.target_id),
    )
    if registry is None:
        return direct

    definition = registry.get(direct.predicate)
    if definition is None:
        return direct

    inverse = registry.inverse_of(direct.predicate)
    if inverse is None:
        return direct

    reverse = FactKey(
        source_id=direct.target_id,
        predicate=inverse,
        target_id=direct.source_id,
    )
    return min((direct, reverse), key=lambda key: key.as_tuple())


def _fact_id(key: FactKey) -> str:
    source = key.source_id.replace("ckb:", "").replace(":", "_")
    target = key.target_id.replace("ckb:", "").replace(":", "_")
    return f"fact:{source}:{key.predicate}:{target}"


def _best_review_status(relationships: list[Any], source_count: int) -> str:
    statuses = [str(row.provenance.get("review_status", "unverified")) for row in relationships]
    active = [status for status in statuses if status != "deprecated"]
    current = max(active or statuses or ["unverified"], key=lambda status: _REVIEW_RANK.get(status, -2))

    # This is a conservative recommendation, not an automatic historical-truth promotion.
    if source_count >= 2 and _REVIEW_RANK.get(current, 0) < _REVIEW_RANK["cross_checked"]:
        return "cross_checked"
    if source_count >= 1 and _REVIEW_RANK.get(current, 0) < _REVIEW_RANK["source_checked"]:
        return "source_checked"
    return current


def aggregate_assertions(
    relationships: Iterable[Any],
    registry: PredicateRegistry | None = None,
) -> AssertionGovernanceReport:
    grouped: dict[FactKey, list[Any]] = defaultdict(list)
    for relationship in relationships:
        grouped[canonical_fact_key(relationship, registry)].append(relationship)

    facts: list[CanonicalFact] = []
    for key, rows in sorted(grouped.items(), key=lambda item: item[0].as_tuple()):
        source_map: dict[tuple[str, str], dict[str, Any]] = {}
        for row in rows:
            for source in row.provenance.get("sources", []):
                if isinstance(source, dict):
                    source_map.setdefault(_source_key(source), dict(source))

        polarities = sorted({_polarity(row) for row in rows})
        confidence = max((float(row.confidence) for row in rows), default=0.0)
        sources = list(source_map.values())
        facts.append(CanonicalFact(
            id=_fact_id(key),
            key=key,
            assertion_ids=sorted(str(row.id) for row in rows),
            sources=sources,
            confidence=confidence,
            review_status=_best_review_status(rows, len(sources)),
            polarities=polarities,
            conflict=len(polarities) > 1,
            duplicate_assertion_count=max(0, len(rows) - 1),
        ))

    return AssertionGovernanceReport(facts=facts)
