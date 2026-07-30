from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable
import argparse
import json

from .graph import Relationship, load_relationships
from .model import Entity, load_entities


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "data" / "canonical"
RELATIONSHIP_ROOT = ROOT / "data" / "relationships"
BATCH_ROOT = ROOT / "data" / "content_batches"

COUNTRY_TAGS = (
    "soviet",
    "russian",
    "german",
    "american",
    "british",
    "french",
    "chinese",
    "japanese",
)


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _source_keys(entity: Entity) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for source in entity.provenance.get("sources", []):
        if isinstance(source, dict):
            keys.add((str(source.get("source_id", "")), str(source.get("url", ""))))
    return keys


def _relationship_source_keys(relationship: Relationship) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for source in relationship.provenance.get("sources", []):
        if isinstance(source, dict):
            keys.add((str(source.get("source_id", "")), str(source.get("url", ""))))
    return keys


def _minimum_integer_target(
    quality_targets: dict[str, Any],
    field_name: str,
    prefix: str,
    errors: list[str],
) -> int:
    raw_value = quality_targets.get(field_name, 0)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{prefix}: {field_name} must be an integer")
        return 0
    if value < 0:
        errors.append(f"{prefix}: {field_name} must be non-negative")
        return 0
    return value


def _boolean_target(
    quality_targets: dict[str, Any],
    field_name: str,
    prefix: str,
    errors: list[str],
) -> bool:
    value = quality_targets.get(field_name, False)
    if not isinstance(value, bool):
        errors.append(f"{prefix}: {field_name} must be a boolean")
        return False
    return value


def missing_core_fields(entity: Entity) -> list[str]:
    missing: list[str] = []
    checks = {
        "identity.canonical_name_en": entity.name_en,
        "identity.canonical_name_zh": entity.name_zh,
        "classification.domain": entity.classification.get("domain"),
        "classification.class": entity.classification.get("class"),
        "classification.subclass": entity.classification.get("subclass"),
        "classification.eras": entity.classification.get("eras"),
        "classification.tags": entity.classification.get("tags"),
        "provenance.review_status": entity.provenance.get("review_status"),
        "provenance.sources": entity.provenance.get("sources"),
        "gameplay.status": (entity.gameplay or {}).get("status"),
        "rights.rights_status": (entity.rights or {}).get("rights_status"),
    }
    for field_name, value in checks.items():
        if value is None or value == "" or value == []:
            missing.append(field_name)
    return missing


def technical_profile_errors(entity: Entity, minimum_claims: int) -> list[str]:
    errors: list[str] = []
    profile = entity.technical
    if not isinstance(profile, dict) or not profile:
        return ["technical profile is required"]
    if not str(profile.get("profile_version", "")).strip():
        errors.append("technical.profile_version is required")
    if not str(profile.get("profile_scope", "")).strip():
        errors.append("technical.profile_scope is required")

    claims = profile.get("claims")
    if not isinstance(claims, list):
        errors.append("technical.claims must be an array")
        return errors
    if len(claims) < minimum_claims:
        errors.append(
            f"technical.claims has {len(claims)} rows; requires at least {minimum_claims}"
        )

    for index, claim in enumerate(claims):
        prefix = f"technical.claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not str(claim.get("field", "")).strip():
            errors.append(f"{prefix}.field is required")
        if claim.get("value") is None:
            errors.append(f"{prefix}.value is required")
        if not str(claim.get("unit", "")).strip():
            errors.append(f"{prefix}.unit is required")
        qualifiers = claim.get("qualifiers")
        if not isinstance(qualifiers, dict):
            errors.append(f"{prefix}.qualifiers must be an object")
        source_urls = claim.get("source_urls")
        if not isinstance(source_urls, list) or not source_urls:
            errors.append(f"{prefix}.source_urls must not be empty")
        elif any(
            not isinstance(url, str) or not url.startswith(("https://", "http://"))
            for url in source_urls
        ):
            errors.append(f"{prefix}.source_urls must contain absolute HTTP URLs")
    return errors


def experience_profile_errors(entity: Entity) -> list[str]:
    errors: list[str] = []
    profile = entity.experience_profile
    if not isinstance(profile, dict) or not profile:
        return ["experience_profile is required"]
    if not str(profile.get("profile_version", "")).strip():
        errors.append("experience_profile.profile_version is required")
    if profile.get("derivation_status") != "derived_from_public_technical_facts":
        errors.append(
            "experience_profile.derivation_status must be "
            "derived_from_public_technical_facts"
        )
    basis_fields = profile.get("basis_fields")
    if not isinstance(basis_fields, list) or not basis_fields:
        errors.append("experience_profile.basis_fields must not be empty")

    dimensions = profile.get("dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        errors.append("experience_profile.dimensions must not be empty")
    else:
        for field_name, value in dimensions.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(
                    f"experience_profile.dimensions.{field_name} must be numeric"
                )
            elif not 0 <= value <= 1:
                errors.append(
                    f"experience_profile.dimensions.{field_name} must be between 0 and 1"
                )

    cues = profile.get("cues")
    if not isinstance(cues, dict) or not cues:
        errors.append("experience_profile.cues must not be empty")
    else:
        for field_name, value in cues.items():
            if not isinstance(value, str) or not value.strip():
                errors.append(f"experience_profile.cues.{field_name} must be text")

    if profile.get("not_game_balance") is not True:
        errors.append("experience_profile.not_game_balance must be true")
    return errors


def load_content_batches(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, dict):
                rows.append(item)
    return rows


def validate_content_batches(
    batches: Iterable[dict[str, Any]],
    entities: Iterable[Entity],
    relationships: Iterable[Relationship],
) -> list[str]:
    errors: list[str] = []
    entity_map = {entity.id: entity for entity in entities}
    relationship_map = {relationship.id: relationship for relationship in relationships}
    seen_batch_ids: set[str] = set()

    for batch in batches:
        batch_id = str(batch.get("batch_id", ""))
        prefix = f"content_batch:{batch_id or '<missing>'}"
        if not batch_id:
            errors.append(f"{prefix}: batch_id is required")
        elif batch_id in seen_batch_ids:
            errors.append(f"{prefix}: duplicate batch_id")
        seen_batch_ids.add(batch_id)

        if not str(batch.get("version", "")).strip():
            errors.append(f"{prefix}: version is required")
        if not str(batch.get("scope", "")).strip():
            errors.append(f"{prefix}: scope is required")

        quality_targets = batch.get("quality_targets", {})
        if not isinstance(quality_targets, dict):
            errors.append(f"{prefix}: quality_targets must be an object")
            quality_targets = {}
        minimum_entity_sources = _minimum_integer_target(
            quality_targets,
            "minimum_sources_per_entity",
            prefix,
            errors,
        )
        minimum_relationship_sources = _minimum_integer_target(
            quality_targets,
            "minimum_sources_per_relationship",
            prefix,
            errors,
        )
        minimum_technical_claims = _minimum_integer_target(
            quality_targets,
            "minimum_technical_claims_per_entity",
            prefix,
            errors,
        )
        require_experience_profile = _boolean_target(
            quality_targets,
            "require_experience_profile",
            prefix,
            errors,
        )

        entity_ids = [str(value) for value in batch.get("entity_ids", [])]
        if not entity_ids:
            errors.append(f"{prefix}: entity_ids must not be empty")
        for entity_id, count in Counter(entity_ids).items():
            if count > 1:
                errors.append(f"{prefix}: duplicate entity id {entity_id}")
            entity = entity_map.get(entity_id)
            if entity is None:
                errors.append(f"{prefix}: unknown entity {entity_id}")
                continue
            for field_name in missing_core_fields(entity):
                errors.append(f"{prefix}: {entity_id} missing core field {field_name}")
            source_count = len(_source_keys(entity))
            if source_count < minimum_entity_sources:
                errors.append(
                    f"{prefix}: {entity_id} has {source_count} independent sources; "
                    f"requires at least {minimum_entity_sources}"
                )
            if minimum_technical_claims:
                for profile_error in technical_profile_errors(
                    entity,
                    minimum_technical_claims,
                ):
                    errors.append(f"{prefix}: {entity_id} {profile_error}")
            if require_experience_profile:
                for profile_error in experience_profile_errors(entity):
                    errors.append(f"{prefix}: {entity_id} {profile_error}")

        rel_ids = [str(value) for value in batch.get("relationship_ids", [])]
        for relationship_id, count in Counter(rel_ids).items():
            if count > 1:
                errors.append(f"{prefix}: duplicate relationship id {relationship_id}")
            relationship = relationship_map.get(relationship_id)
            if relationship is None:
                errors.append(f"{prefix}: unknown relationship {relationship_id}")
                continue
            source_count = len(_relationship_source_keys(relationship))
            if source_count < minimum_relationship_sources:
                errors.append(
                    f"{prefix}: {relationship_id} has {source_count} independent sources; "
                    f"requires at least {minimum_relationship_sources}"
                )

    return errors


def build_content_report(
    entities: Iterable[Entity],
    relationships: Iterable[Relationship],
    batches: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    entity_rows = list(entities)
    relationship_rows = list(relationships)
    batch_rows = list(batches)
    ground_vehicles = [
        entity
        for entity in entity_rows
        if entity.entity_type == "platform"
        and entity.classification.get("class") == "GroundVehicle"
    ]

    country_counts = Counter()
    review_counts = Counter()
    missing_core: dict[str, list[str]] = {}
    source_covered = 0
    multi_source_covered = 0
    technical_populated = 0
    technical_claim_count = 0
    experience_covered = 0
    derived_experience_covered = 0
    embedded_relationship_count = 0

    for entity in entity_rows:
        tags = {str(value) for value in entity.classification.get("tags", [])}
        for country in COUNTRY_TAGS:
            if country in tags:
                country_counts[country] += 1
        review_counts[str(entity.provenance.get("review_status", "missing"))] += 1

        missing = missing_core_fields(entity)
        if missing:
            missing_core[entity.id] = missing

        source_count = len(_source_keys(entity))
        source_covered += int(source_count >= 1)
        multi_source_covered += int(source_count >= 2)
        technical_populated += int(bool(entity.technical))
        if isinstance(entity.technical, dict):
            claims = entity.technical.get("claims", [])
            if isinstance(claims, list):
                technical_claim_count += len(claims)
        experience_covered += int(bool(entity.experience_profile))
        derived_experience_covered += int(
            isinstance(entity.experience_profile, dict)
            and entity.experience_profile.get("derivation_status")
            == "derived_from_public_technical_facts"
        )
        embedded_relationship_count += len(entity.relationships)

    relationship_review_counts = Counter()
    relationship_source_covered = 0
    relationship_multi_source_covered = 0
    for relationship in relationship_rows:
        relationship_review_counts[
            str(relationship.provenance.get("review_status", "missing"))
        ] += 1
        source_count = len(_relationship_source_keys(relationship))
        relationship_source_covered += int(source_count >= 1)
        relationship_multi_source_covered += int(source_count >= 2)

    batched_entity_ids = {
        str(entity_id)
        for batch in batch_rows
        for entity_id in batch.get("entity_ids", [])
    }
    ground_vehicle_ids = {entity.id for entity in ground_vehicles}
    unbatched_ground_vehicle_ids = sorted(ground_vehicle_ids - batched_entity_ids)
    independent_relationship_count = len(relationship_rows)
    total_relationship_count = embedded_relationship_count + independent_relationship_count

    return {
        "report_version": "1.2",
        "entity_count": len(entity_rows),
        "ground_vehicle_count": len(ground_vehicles),
        "country_counts": dict(sorted(country_counts.items())),
        "review_status_counts": dict(sorted(review_counts.items())),
        "core_complete_count": len(entity_rows) - len(missing_core),
        "core_completeness_rate": _ratio(
            len(entity_rows) - len(missing_core),
            len(entity_rows),
        ),
        "missing_core_count": len(missing_core),
        "missing_core_entities": dict(sorted(missing_core.items())),
        "source_covered_count": source_covered,
        "source_coverage_rate": _ratio(source_covered, len(entity_rows)),
        "multi_source_covered_count": multi_source_covered,
        "multi_source_coverage_rate": _ratio(multi_source_covered, len(entity_rows)),
        "technical_populated_count": technical_populated,
        "technical_coverage_rate": _ratio(technical_populated, len(entity_rows)),
        "technical_claim_count": technical_claim_count,
        "experience_profile_covered_count": experience_covered,
        "experience_profile_coverage_rate": _ratio(
            experience_covered,
            len(entity_rows),
        ),
        "derived_experience_profile_count": derived_experience_covered,
        "derived_experience_profile_rate": _ratio(
            derived_experience_covered,
            len(entity_rows),
        ),
        "embedded_relationship_count": embedded_relationship_count,
        "independent_relationship_count": independent_relationship_count,
        "independent_relationship_rate": _ratio(
            independent_relationship_count,
            total_relationship_count,
        ),
        "relationship_review_status_counts": dict(
            sorted(relationship_review_counts.items())
        ),
        "relationship_source_covered_count": relationship_source_covered,
        "relationship_source_coverage_rate": _ratio(
            relationship_source_covered,
            independent_relationship_count,
        ),
        "relationship_multi_source_covered_count": relationship_multi_source_covered,
        "relationship_multi_source_coverage_rate": _ratio(
            relationship_multi_source_covered,
            independent_relationship_count,
        ),
        "content_batch_count": len(batch_rows),
        "batched_entity_count": len(batched_entity_ids),
        "unbatched_ground_vehicle_count": len(unbatched_ground_vehicle_ids),
        "unbatched_ground_vehicle_ids": unbatched_ground_vehicle_ids,
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-content-audit")
    parser.add_argument("--canonical", type=Path, default=CANONICAL_ROOT)
    parser.add_argument("--relationships", type=Path, default=RELATIONSHIP_ROOT)
    parser.add_argument("--batches", type=Path, default=BATCH_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    entities = load_entities(args.canonical)
    relationships = load_relationships(args.relationships)
    batches = load_content_batches(args.batches)
    errors = validate_content_batches(batches, entities, relationships)
    report = build_content_report(entities, relationships, batches)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    for error in errors:
        print("ERROR:", error)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
