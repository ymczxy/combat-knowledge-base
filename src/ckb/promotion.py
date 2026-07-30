from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import json

from .candidates import CandidateEntity, stable_slug


@dataclass(frozen=True, slots=True)
class PromotionProposal:
    candidate_id: str
    proposed_id: str
    canonical_name_en: str
    canonical_name_zh: str
    entity_type: str
    classification: dict[str, object]
    external_ids: dict[str, str]
    sources: tuple[dict[str, str], ...]
    confidence: float
    promotion_status: str
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "proposed_id": self.proposed_id,
            "identity": {
                "canonical_name_en": self.canonical_name_en,
                "canonical_name_zh": self.canonical_name_zh,
                "aliases": [],
                "external_ids": self.external_ids,
            },
            "entity_type": self.entity_type,
            "classification": self.classification,
            "provenance": {
                "review_status": self.promotion_status,
                "confidence": self.confidence,
                "sources": list(self.sources),
                "candidate_id": self.candidate_id,
                "blockers": list(self.blockers),
            },
            "relationships": [],
        }


def _entity_type(candidate: CandidateEntity) -> str:
    return candidate.domain if candidate.domain in {"Weapon", "Platform", "System", "Ammunition", "Material", "Component"} else "Entity"


def proposal_from_decision(candidate: CandidateEntity, decision: dict[str, object]) -> PromotionProposal:
    final = str(decision.get("final_decision") or decision.get("decision") or "human_review")
    score = float(decision.get("adjusted_score") or decision.get("score") or 0.0)
    label = str(decision.get("external_label") or candidate.source_name)
    source = str(decision.get("external_source") or "unknown")
    external_id = str(decision.get("external_id") or "")
    url = str(decision.get("external_url") or "")
    blockers: list[str] = []
    if candidate.resolution_status == "ambiguous":
        blockers.append("candidate_ambiguity")
    if final != "auto_accept":
        blockers.append("identity_not_auto_accepted")
    if not external_id:
        blockers.append("missing_external_id")
    status = "promotion_ready" if not blockers and score >= 0.90 else "review_required"
    proposed = str(decision.get("suggested_canonical_id") or f"ckb:{candidate.domain.casefold()}:{candidate.class_name.casefold()}:{stable_slug(label)}")
    return PromotionProposal(
        candidate_id=candidate.candidate_id,
        proposed_id=proposed,
        canonical_name_en=label,
        canonical_name_zh="",
        entity_type=_entity_type(candidate),
        classification={
            "domain": candidate.domain,
            "class": candidate.class_name,
            "subclass": candidate.subclass,
            "eras": list(candidate.eras),
            "tags": ["promotion_proposal", candidate.source_group],
        },
        external_ids={source: external_id} if external_id else {},
        sources=({"source_id": source, "url": url},),
        confidence=score,
        promotion_status=status,
        blockers=tuple(blockers),
    )


def build_proposals(candidates: Iterable[CandidateEntity], decisions: Iterable[dict[str, object]]) -> list[PromotionProposal]:
    candidate_map = {row.candidate_id: row for row in candidates}
    best: dict[str, dict[str, object]] = {}
    for row in decisions:
        candidate_id = str(row.get("candidate_id", ""))
        if candidate_id not in candidate_map:
            continue
        score = float(row.get("adjusted_score") or row.get("score") or 0.0)
        current = best.get(candidate_id)
        current_score = float(current.get("adjusted_score") or current.get("score") or 0.0) if current else -1.0
        if score > current_score:
            best[candidate_id] = row
    return [proposal_from_decision(candidate_map[key], row) for key, row in sorted(best.items())]


def write_promotion_bundle(proposals: Iterable[PromotionProposal], output: Path) -> None:
    rows = list(proposals)
    output.mkdir(parents=True, exist_ok=True)
    ready = [row.to_dict() for row in rows if row.promotion_status == "promotion_ready"]
    review = [row.to_dict() for row in rows if row.promotion_status != "promotion_ready"]
    (output / "proposals.json").write_text(json.dumps([row.to_dict() for row in rows], ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "promotion_ready.json").write_text(json.dumps(ready, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "review_required.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"format_version": 1, "proposal_count": len(rows), "promotion_ready_count": len(ready), "review_required_count": len(review)}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
