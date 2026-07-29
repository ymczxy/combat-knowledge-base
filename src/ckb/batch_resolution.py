from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
import json

from .adapters import SourceHit
from .candidates import CandidateEntity
from .constraints import ConstraintResult, evaluate_constraints
from .resolution import MatchDecision, SearchCache, decide_matches


@dataclass(frozen=True, slots=True)
class ConstrainedDecision:
    base: MatchDecision
    constraint: ConstraintResult
    adjusted_score: float
    final_decision: str

    def to_dict(self) -> dict[str, object]:
        row = self.base.to_dict()
        row["constraint"] = asdict(self.constraint)
        row["adjusted_score"] = self.adjusted_score
        row["final_decision"] = self.final_decision
        return row


def apply_constraints(candidate: CandidateEntity, hits: Iterable[SourceHit]) -> list[ConstrainedDecision]:
    hit_rows = list(hits)
    base_rows = decide_matches(candidate, hit_rows)
    by_key = {(hit.source, hit.external_id): hit for hit in hit_rows}
    output: list[ConstrainedDecision] = []

    for base in base_rows:
        hit = by_key[(base.external_source, base.external_id)]
        constraint = evaluate_constraints(candidate, hit)
        adjusted = round(max(0.0, min(1.0, base.score + constraint.adjustment)), 6)

        if not constraint.compatible:
            final = "reject" if adjusted < 0.62 else "human_review"
        elif candidate.resolution_status == "ambiguous":
            final = "human_review" if adjusted >= 0.62 else "reject"
        elif base.rank == 1 and adjusted >= 0.90 and base.margin_to_next >= 0.08:
            final = "auto_accept"
        elif adjusted >= 0.62:
            final = "human_review"
        else:
            final = "reject"

        output.append(ConstrainedDecision(base, constraint, adjusted, final))

    return sorted(output, key=lambda row: row.adjusted_score, reverse=True)


def resolve_cached_candidates(
    candidates: Iterable[CandidateEntity],
    cache: SearchCache,
    source: str = "wikidata",
    language: str = "en",
) -> tuple[list[ConstrainedDecision], list[dict[str, str]]]:
    decisions: list[ConstrainedDecision] = []
    missing: list[dict[str, str]] = []
    for candidate in candidates:
        hits = cache.get(source, candidate.source_name, language)
        if hits is None:
            missing.append({
                "candidate_id": candidate.candidate_id,
                "query": candidate.source_name,
                "source": source,
                "language": language,
            })
            continue
        decisions.extend(apply_constraints(candidate, hits))
    return decisions, missing


def write_batch_bundle(
    decisions: Iterable[ConstrainedDecision],
    missing: Iterable[dict[str, str]],
    output: Path,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows = [row.to_dict() for row in decisions]
    missing_rows = list(missing)
    review = [row for row in rows if row["final_decision"] == "human_review"]
    accepted = [row for row in rows if row["final_decision"] == "auto_accept"]
    rejected = [row for row in rows if row["final_decision"] == "reject"]

    (output / "decisions.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "accepted.json").write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "review_queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "rejected.json").write_text(json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "missing_cache.json").write_text(json.dumps(missing_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "format_version": 1,
        "decision_count": len(rows),
        "auto_accept_count": len(accepted),
        "human_review_count": len(review),
        "reject_count": len(rejected),
        "missing_cache_count": len(missing_rows),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
