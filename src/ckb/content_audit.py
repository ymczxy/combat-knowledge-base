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
    relationship_ids = {relationship.id for relationship in relationships}
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
        minimum_sources = 0
        if isinstance(quality_targets, dict):
            raw_minimum_sources = quality_targets.get("minimum_sources_per_entity", 0)
            try:
                minimum_sources = int(raw_minimum_sources)
            except (TypeError, ValueError):
                errors.append(f"{prefix}: minimum_sources_per_entity must be an integer")
                minimum_sources = 0
            if minimum_sources < 0:
                errors.append(f"{prefix}: minimum_sources_per_entity must be non-negative")
                minimum_sources = 0

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
            if source_count < minimum_sources:
                errors.append(
                    f"{prefix}: {entity_id} has {source_count} independent sources; "
                    f"requires at least {minimum_sources}"
                )

        rel_ids = [str(value) for value in batch.get("relationship_ids", [])]
        for relationship_id, count in Counter(rel_ids).items():
            if count > 1:
                errors.append(f"{prefix}: duplicate relationship id {relationship_id}")
            if relationship_id not in relationship_ids:
                errors.append(f"{prefix}: unknown relationship {relationship_id}")

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
    experience_covered = 0
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
        experience_covered += int(bool(entity.experience_profile))
        embedded_relationship_count += len(entity.relationships)

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
        "report_version": "1.0",
        "entity_count": len(entity_rows),
        "ground_vehicle_count": len(ground_vehicles),
        "country_counts": dict(sorted(country_counts.items())),
        "review_status_counts": dict(sorted(review_counts.items())),
        "core_complete_count": len(entity_rows) - len(missing_core),
        "core_completeness_rate": _ratio(len(entity_rows) - len(missing_core), len(entity_rows)),
        "missing_core_count": len(missing_core),
        "missing_core_entities": dict(sorted(missing_core.items())),
        "source_covered_count": source_covered,
        "source_coverage_rate": _ratio(source_covered, len(entity_rows)),
        "multi_source_covered_count": multi_source_covered,
        "multi_source_coverage_rate": _ratio(multi_source_covered, len(entity_rows)),
        "technical_populated_count": technical_populated,
        "technical_coverage_rate": _ratio(technical_populated, len(entity_rows)),
        "experience_profile_covered_count": experience_covered,
        "experience_profile_coverage_rate": _ratio(experience_covered, len(entity_rows)),
        "embedded_relationship_count": embedded_relationship_count,
        "independent_relationship_count": independent_relationship_count,
        "independent_relationship_rate": _ratio(independent_relationship_count, total_relationship_count),
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
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    for error in errors:
        print("ERROR:", error)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
