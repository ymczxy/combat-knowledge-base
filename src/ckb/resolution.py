from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from typing import Iterable
import json
import re

from .adapters import SourceHit
from .candidates import CandidateEntity, normalize_name, stable_slug

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_FAMILY_WORDS = {"class", "family", "series", "type", "model", "mark", "mk", "block", "variant"}
DOMAIN_HINTS: dict[str, set[str]] = {
    "Weapon": {"weapon", "rifle", "gun", "missile", "artillery", "sword", "bow", "grenade", "cannon"},
    "Platform": {"tank", "aircraft", "fighter", "bomber", "destroyer", "submarine", "vehicle", "ship", "helicopter", "uav"},
    "System": {"radar", "sensor", "fire control", "electronic warfare", "system", "aegis"},
}
CLASS_HINTS: dict[str, set[str]] = {
    "Firearm": {"rifle", "gun", "pistol", "carbine", "machine gun", "firearm"},
    "Missile": {"missile", "interceptor", "rocket", "surface-to-air", "anti-tank"},
    "GroundVehicle": {"tank", "armoured", "armored", "vehicle", "ifv", "apc"},
    "Aircraft": {"aircraft", "fighter", "bomber", "helicopter", "airplane"},
    "NavalPlatform": {"ship", "destroyer", "cruiser", "submarine", "carrier", "frigate"},
    "MeleeWeapon": {"sword", "spear", "blade", "axe", "mace", "weapon"},
}


@dataclass(frozen=True, slots=True)
class MatchScore:
    total: float
    name_similarity: float
    token_overlap: float
    alias_bonus: float
    context_bonus: float
    ambiguity_penalty: float


@dataclass(frozen=True, slots=True)
class MatchDecision:
    candidate_id: str
    source_name: str
    source_group: str
    external_source: str
    external_id: str
    external_label: str
    external_url: str
    score: float
    score_breakdown: MatchScore
    rank: int
    margin_to_next: float
    decision: str
    suggested_canonical_id: str | None
    entity_scope: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        row = asdict(self)
        row["score_breakdown"] = asdict(self.score_breakdown)
        row["reasons"] = list(self.reasons)
        return row


def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall(normalize_name(value)))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def infer_entity_scope(candidate_name: str, hit: SourceHit) -> str:
    text = normalize_name(" ".join([candidate_name, hit.label, hit.description]))
    tokens = _tokens(text)
    if "class" in tokens and any(word in tokens for word in {"ship", "destroyer", "submarine", "cruiser", "carrier"}):
        return "class"
    if any(word in tokens for word in {"family", "series"}):
        return "family"
    if any(word in tokens for word in {"prototype", "experimental", "demonstrator"}):
        return "prototype"
    if any(word in tokens for word in {"variant", "model", "mark", "mk", "block"}):
        return "variant"
    return "model"


def score_hit(candidate: CandidateEntity, hit: SourceHit) -> MatchScore:
    candidate_name = normalize_name(candidate.source_name)
    hit_name = normalize_name(hit.label)
    name_similarity = SequenceMatcher(None, candidate_name, hit_name).ratio()
    token_overlap = _jaccard(_tokens(candidate_name), _tokens(hit_name))

    alias_scores = [SequenceMatcher(None, candidate_name, normalize_name(alias)).ratio() for alias in hit.aliases]
    alias_bonus = max(alias_scores, default=0.0) * 0.12

    context = normalize_name(f"{hit.label} {hit.description}")
    context_bonus = 0.0
    domain_hits = DOMAIN_HINTS.get(candidate.domain, set())
    class_hits = CLASS_HINTS.get(candidate.class_name, set())
    if any(hint in context for hint in domain_hits):
        context_bonus += 0.08
    if any(hint in context for hint in class_hits):
        context_bonus += 0.10

    ambiguity_penalty = 0.12 if candidate.resolution_status == "ambiguous" else 0.0
    if candidate.domain == "Mixed":
        ambiguity_penalty += 0.08

    total = 0.58 * name_similarity + 0.22 * token_overlap + alias_bonus + context_bonus - ambiguity_penalty
    total = max(0.0, min(1.0, total))
    return MatchScore(
        total=round(total, 6),
        name_similarity=round(name_similarity, 6),
        token_overlap=round(token_overlap, 6),
        alias_bonus=round(alias_bonus, 6),
        context_bonus=round(context_bonus, 6),
        ambiguity_penalty=round(ambiguity_penalty, 6),
    )


def suggested_canonical_id(candidate: CandidateEntity, hit: SourceHit) -> str:
    domain = candidate.domain.casefold() if candidate.domain != "Mixed" else "unresolved"
    class_name = candidate.class_name.casefold() if candidate.class_name != "Unresolved" else "entity"
    return f"ckb:{domain}:{class_name}:{stable_slug(hit.label or candidate.source_name)}"


def decide_matches(candidate: CandidateEntity, hits: Iterable[SourceHit]) -> list[MatchDecision]:
    scored = sorted(((hit, score_hit(candidate, hit)) for hit in hits), key=lambda row: row[1].total, reverse=True)
    decisions: list[MatchDecision] = []
    for index, (hit, score) in enumerate(scored):
        next_score = scored[index + 1][1].total if index + 1 < len(scored) else 0.0
        margin = round(score.total - next_score, 6)
        reasons: list[str] = []
        if score.name_similarity >= 0.95:
            reasons.append("near_exact_name")
        if score.token_overlap >= 0.8:
            reasons.append("strong_token_overlap")
        if score.alias_bonus > 0.08:
            reasons.append("alias_match")
        if score.context_bonus >= 0.10:
            reasons.append("class_context_match")
        if candidate.resolution_status == "ambiguous":
            reasons.append("candidate_requires_disambiguation")

        if candidate.resolution_status == "ambiguous" and index == 0:
            # The best external hit for an ambiguous catalog entry must remain visible
            # to a reviewer even when the ambiguity penalty pushes its score below the
            # normal review threshold. Lower-ranked weak hits can still be rejected.
            decision = "human_review"
        elif index == 0 and score.total >= 0.90 and margin >= 0.08:
            decision = "auto_accept"
        elif score.total >= 0.62:
            decision = "human_review"
        else:
            decision = "reject"

        decisions.append(MatchDecision(
            candidate_id=candidate.candidate_id,
            source_name=candidate.source_name,
            source_group=candidate.source_group,
            external_source=hit.source,
            external_id=hit.external_id,
            external_label=hit.label,
            external_url=hit.url,
            score=score.total,
            score_breakdown=score,
            rank=index + 1,
            margin_to_next=margin,
            decision=decision,
            suggested_canonical_id=suggested_canonical_id(candidate, hit) if decision != "reject" else None,
            entity_scope=infer_entity_scope(candidate.source_name, hit),
            reasons=tuple(reasons),
        ))
    return decisions


def write_resolution_bundle(decisions: Iterable[MatchDecision], output: Path) -> None:
    rows = list(decisions)
    output.mkdir(parents=True, exist_ok=True)
    payload = [row.to_dict() for row in rows]
    (output / "decisions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    review = [row for row in payload if row["decision"] == "human_review"]
    accepted = [row for row in payload if row["decision"] == "auto_accept"]
    manifest = {
        "format_version": 1,
        "decision_count": len(rows),
        "auto_accept_count": len(accepted),
        "human_review_count": len(review),
        "reject_count": sum(row["decision"] == "reject" for row in payload),
        "content_sha256": sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
    }
    (output / "review_queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


class SearchCache:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, source: str, query: str, language: str) -> Path:
        digest = sha256(f"{source}\0{language}\0{normalize_name(query)}".encode("utf-8")).hexdigest()[:20]
        return self.root / source / language / f"{digest}.json"

    def get(self, source: str, query: str, language: str = "en") -> list[SourceHit] | None:
        path = self._path(source, query, language)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return [SourceHit(**{**row, "aliases": tuple(row.get("aliases", []))}) for row in data.get("hits", [])]

    def put(self, source: str, query: str, hits: Iterable[SourceHit], language: str = "en") -> Path:
        path = self._path(source, query, language)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [asdict(hit) for hit in hits]
        payload = {"source": source, "query": query, "language": language, "hits": rows}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
