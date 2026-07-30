from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import argparse
import hashlib
import json
import re

from .export import load_profile
from .model import Entity, load_entities
from .technical import NORMALIZATION_VERSION, build_technical_comparison
from .technical_metrics import build_derived_metrics, load_metric_specs


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "data" / "canonical"
DEFAULT_PROFILE = ROOT / "data" / "curated" / "destory" / "build_profile.json"
BUNDLE_SCHEMA_VERSION = "1.0"
BUNDLE_FORMAT = "ckb.godot.runtime"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    lowered = value.strip().casefold()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return cleaned or "default"


def _configuration_label(qualifiers: Any) -> str:
    if isinstance(qualifiers, dict):
        value = qualifiers.get("configuration")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "default"


def _configuration_id(entity_id: str, label: str) -> str:
    digest = _sha256_text(f"{entity_id}\n{label}")[:10]
    return f"{entity_id}#cfg:{_slug(label)}:{digest}"


def _claim_ref(entity_id: str, claim_index: int) -> str:
    return f"{entity_id}#claim:{claim_index}"


def _runtime_config(profile: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    config = profile.get("godot_runtime_bundle")
    if not isinstance(config, dict):
        return {}, ["profile.godot_runtime_bundle must be an object"]
    if config.get("enabled") is not True:
        errors.append("profile.godot_runtime_bundle.enabled must be true")
    bundle_id = str(config.get("bundle_id", "")).strip()
    if not bundle_id:
        errors.append("profile.godot_runtime_bundle.bundle_id is required")
    entity_ids = config.get("entity_ids")
    if not isinstance(entity_ids, list) or not entity_ids:
        errors.append("profile.godot_runtime_bundle.entity_ids must not be empty")
    elif any(not isinstance(value, str) or not value.strip() for value in entity_ids):
        errors.append("profile.godot_runtime_bundle.entity_ids must contain non-empty strings")
    elif len(entity_ids) != len(set(entity_ids)):
        errors.append("profile.godot_runtime_bundle.entity_ids contains duplicates")
    allowed_statuses = config.get(
        "allowed_review_statuses",
        ["source_checked", "cross_checked", "expert_reviewed"],
    )
    if not isinstance(allowed_statuses, list) or not allowed_statuses:
        errors.append("profile.godot_runtime_bundle.allowed_review_statuses must not be empty")
    metric_specs = str(config.get("derived_metric_specs", "")).strip()
    if not metric_specs:
        errors.append("profile.godot_runtime_bundle.derived_metric_specs is required")
    return config, errors


def _selected_entities(
    entities: Iterable[Entity],
    config: dict[str, Any],
) -> tuple[list[Entity], list[str]]:
    entity_map = {entity.id: entity for entity in entities}
    entity_ids = [str(value) for value in config.get("entity_ids", [])]
    allowed_statuses = {
        str(value)
        for value in config.get(
            "allowed_review_statuses",
            ["source_checked", "cross_checked", "expert_reviewed"],
        )
    }
    selected: list[Entity] = []
    errors: list[str] = []
    for entity_id in entity_ids:
        entity = entity_map.get(entity_id)
        if entity is None:
            errors.append(f"runtime entity is unknown: {entity_id}")
            continue
        review_status = str(entity.provenance.get("review_status", ""))
        if review_status not in allowed_statuses:
            errors.append(
                f"runtime entity {entity_id} has review_status {review_status or '<missing>'}; "
                f"allowed: {sorted(allowed_statuses)}"
            )
            continue
        selected.append(entity)
    return selected, errors


def _source_table(urls: Iterable[str]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    ordered = sorted({str(url) for url in urls if str(url)})
    table = [{"ref": index, "url": url} for index, url in enumerate(ordered)]
    return table, {row["url"]: int(row["ref"]) for row in table}


def _runtime_claim(
    row: dict[str, Any],
    source_refs: dict[str, int],
) -> dict[str, Any]:
    entity_id = str(row["entity_id"])
    qualifiers = row.get("qualifiers", {})
    label = _configuration_label(qualifiers)
    normalized = row.get("normalized")
    if isinstance(normalized, dict):
        value = normalized.get("value")
        unit = normalized.get("unit")
        kind = "normalized_numeric"
    else:
        original = row.get("original", {})
        value = original.get("value")
        unit = original.get("unit")
        kind = "descriptive"
    return {
        "claim_ref": _claim_ref(entity_id, int(row["claim_index"])),
        "claim_index": int(row["claim_index"]),
        "field": str(row["field"]),
        "kind": kind,
        "value": value,
        "unit": unit,
        "qualifiers": qualifiers,
        "configuration_id": _configuration_id(entity_id, label),
        "source_refs": [
            source_refs[str(url)]
            for url in row.get("source_urls", [])
            if str(url) in source_refs
        ],
    }


def _runtime_metric(
    row: dict[str, Any],
    source_refs: dict[str, int],
) -> dict[str, Any]:
    entity_id = str(row["entity_id"])
    qualifiers = row.get("qualifiers", {})
    label = _configuration_label(qualifiers)
    inputs = row.get("inputs", {})
    power = inputs.get("power", {}) if isinstance(inputs, dict) else {}
    mass = inputs.get("mass", {}) if isinstance(inputs, dict) else {}
    return {
        "metric_ref": str(row["metric_id"]),
        "metric": str(row["metric"]),
        "formula": str(row["formula"]),
        "value": row.get("value"),
        "unit": row.get("unit"),
        "qualifiers": qualifiers,
        "configuration_id": _configuration_id(entity_id, label),
        "input_claim_refs": [
            _claim_ref(entity_id, int(power["claim_index"])),
            _claim_ref(entity_id, int(mass["claim_index"])),
        ],
        "source_refs": [
            source_refs[str(url)]
            for url in row.get("source_urls", [])
            if str(url) in source_refs
        ],
        "derivation_status": row.get("derivation_status"),
        "not_source_fact": row.get("not_source_fact") is True,
        "not_game_balance": row.get("not_game_balance") is True,
    }


def _runtime_experience(entity: Entity, include: bool) -> dict[str, Any] | None:
    profile = entity.experience_profile
    if not include or not isinstance(profile, dict) or not profile:
        return None
    return {
        "profile_version": profile.get("profile_version"),
        "derivation_status": profile.get("derivation_status"),
        "basis_fields": profile.get("basis_fields", []),
        "dimensions": profile.get("dimensions", {}),
        "cues": profile.get("cues", {}),
        "not_game_balance": profile.get("not_game_balance") is True,
    }


def build_godot_runtime_bundle(
    entities: Iterable[Entity],
    profile: dict[str, Any],
    *,
    project_root: Path = ROOT,
) -> tuple[dict[str, Any] | None, list[str]]:
    entity_rows = list(entities)
    config, errors = _runtime_config(profile)
    if errors:
        return None, errors

    selected, selection_errors = _selected_entities(entity_rows, config)
    errors.extend(selection_errors)
    if errors:
        return None, errors

    include_fields = config.get("technical_fields", [])
    if not isinstance(include_fields, list):
        return None, ["profile.godot_runtime_bundle.technical_fields must be an array"]
    technical = build_technical_comparison(
        selected,
        fields=[str(value) for value in include_fields],
    )
    if technical["summary"]["unsupported_numeric_count"]:
        for row in technical["unsupported_numeric_claims"]:
            errors.append(
                f"{row['entity_id']} claim {row['claim_index']} {row['field']}: "
                f"{row['normalization_error']}"
            )

    metric_path = project_root / str(config["derived_metric_specs"])
    if not metric_path.exists():
        errors.append(f"derived metric specification does not exist: {metric_path}")
        return None, errors
    metric_specification = load_metric_specs(metric_path)
    metrics = build_derived_metrics(selected, metric_specification)
    errors.extend(str(value) for value in metrics.get("errors", []))
    if errors:
        return None, errors

    all_urls = [
        str(url)
        for row in technical["rows"]
        for url in row.get("source_urls", [])
    ] + [
        str(url)
        for row in metrics["rows"]
        for url in row.get("source_urls", [])
    ]
    source_table, source_refs = _source_table(all_urls)

    technical_by_entity: dict[str, list[dict[str, Any]]] = {
        entity.id: [] for entity in selected
    }
    for row in technical["rows"]:
        technical_by_entity[str(row["entity_id"])].append(
            _runtime_claim(row, source_refs)
        )

    metrics_by_entity: dict[str, list[dict[str, Any]]] = {
        entity.id: [] for entity in selected
    }
    for row in metrics["rows"]:
        metrics_by_entity[str(row["entity_id"])].append(
            _runtime_metric(row, source_refs)
        )

    include_experience = config.get("include_experience_profile", False) is True
    runtime_entities: list[dict[str, Any]] = []
    configuration_count = 0
    for entity in selected:
        claims = sorted(
            technical_by_entity[entity.id],
            key=lambda row: (row["claim_index"], row["claim_ref"]),
        )
        metric_rows = sorted(
            metrics_by_entity[entity.id],
            key=lambda row: row["metric_ref"],
        )
        configuration_rows = {
            row["configuration_id"]: _configuration_label(row.get("qualifiers", {}))
            for row in [*claims, *metric_rows]
        }
        configurations = [
            {"configuration_id": config_id, "label": label}
            for config_id, label in sorted(configuration_rows.items())
        ]
        configuration_count += len(configurations)
        experience = _runtime_experience(entity, include_experience)
        runtime_entity: dict[str, Any] = {
            "id": entity.id,
            "entity_type": entity.entity_type,
            "display_name": {"en": entity.name_en, "zh": entity.name_zh},
            "classification": {
                "class": entity.classification.get("class"),
                "subclass": entity.classification.get("subclass"),
                "eras": entity.classification.get("eras", []),
                "tags": entity.classification.get("tags", []),
            },
            "configurations": configurations,
            "technical_claims": claims,
            "derived_metrics": metric_rows,
        }
        if experience is not None:
            runtime_entity["experience_profile"] = experience
        runtime_entities.append(runtime_entity)

    payload = {
        "source_table": source_table,
        "entities": runtime_entities,
    }
    content_sha256 = _sha256_text(_canonical_json(payload))
    bundle = {
        "manifest": {
            "bundle_format": BUNDLE_FORMAT,
            "bundle_id": str(config["bundle_id"]),
            "profile_id": str(profile.get("profile_id", "unknown")),
            "format_version": int(config.get("format_version", 1)),
            "schema_version": BUNDLE_SCHEMA_VERSION,
            "technical_normalization_version": NORMALIZATION_VERSION,
            "metric_spec_version": metrics.get("spec_version"),
            "entity_count": len(runtime_entities),
            "configuration_count": configuration_count,
            "technical_claim_count": technical["summary"]["claim_count"],
            "normalized_numeric_claim_count": technical["summary"][
                "normalized_numeric_claim_count"
            ],
            "descriptive_claim_count": technical["summary"]["descriptive_claim_count"],
            "derived_metric_count": metrics["summary"]["derived_metric_count"],
            "source_ref_count": len(source_table),
            "content_sha256": content_sha256,
            "boundaries": {
                "contains_source_documents": False,
                "contains_game_balance": False,
                "derived_metrics_are_source_facts": False,
                "runtime_values_require_configuration_qualifiers": True,
            },
        },
        **payload,
    }
    errors.extend(validate_godot_runtime_bundle(bundle))
    return (bundle if not errors else None), errors


def validate_godot_runtime_bundle(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest = bundle.get("manifest")
    entities = bundle.get("entities")
    source_table = bundle.get("source_table")
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    if not isinstance(entities, list):
        return ["entities must be an array"]
    if not isinstance(source_table, list):
        return ["source_table must be an array"]

    source_refs = {
        row.get("ref")
        for row in source_table
        if isinstance(row, dict)
        and isinstance(row.get("ref"), int)
        and isinstance(row.get("url"), str)
        and row.get("url")
    }
    if len(source_refs) != len(source_table):
        errors.append("source_table contains invalid or duplicate refs")

    claim_refs: set[str] = set()
    metric_refs: set[str] = set()
    configuration_count = 0
    claim_count = 0
    normalized_count = 0
    descriptive_count = 0
    metric_count = 0

    forbidden_entity_keys = {"provenance", "rights", "gameplay", "raw"}
    for entity in entities:
        if not isinstance(entity, dict):
            errors.append("entity row must be an object")
            continue
        present_forbidden = sorted(forbidden_entity_keys & set(entity))
        if present_forbidden:
            errors.append(
                f"{entity.get('id', '<missing>')} contains forbidden runtime keys "
                f"{present_forbidden}"
            )
        configurations = entity.get("configurations", [])
        if not isinstance(configurations, list):
            errors.append(f"{entity.get('id', '<missing>')} configurations must be an array")
            configurations = []
        config_ids = {
            row.get("configuration_id")
            for row in configurations
            if isinstance(row, dict) and isinstance(row.get("configuration_id"), str)
        }
        if len(config_ids) != len(configurations):
            errors.append(f"{entity.get('id', '<missing>')} configurations are invalid")
        configuration_count += len(configurations)

        local_claim_refs: set[str] = set()
        claims = entity.get("technical_claims", [])
        if not isinstance(claims, list):
            errors.append(f"{entity.get('id', '<missing>')} technical_claims must be an array")
            claims = []
        for claim in claims:
            if not isinstance(claim, dict):
                errors.append("technical claim must be an object")
                continue
            ref = claim.get("claim_ref")
            if not isinstance(ref, str) or not ref:
                errors.append("technical claim_ref is required")
                continue
            if ref in claim_refs:
                errors.append(f"duplicate technical claim_ref {ref}")
            claim_refs.add(ref)
            local_claim_refs.add(ref)
            claim_count += 1
            kind = claim.get("kind")
            normalized_count += int(kind == "normalized_numeric")
            descriptive_count += int(kind == "descriptive")
            if kind not in {"normalized_numeric", "descriptive"}:
                errors.append(f"{ref} has invalid kind {kind}")
            if claim.get("configuration_id") not in config_ids:
                errors.append(f"{ref} references unknown configuration")
            for source_ref in claim.get("source_refs", []):
                if source_ref not in source_refs:
                    errors.append(f"{ref} references unknown source ref {source_ref}")

        metrics = entity.get("derived_metrics", [])
        if not isinstance(metrics, list):
            errors.append(f"{entity.get('id', '<missing>')} derived_metrics must be an array")
            metrics = []
        for metric in metrics:
            if not isinstance(metric, dict):
                errors.append("derived metric must be an object")
                continue
            ref = metric.get("metric_ref")
            if not isinstance(ref, str) or not ref:
                errors.append("derived metric_ref is required")
                continue
            if ref in metric_refs:
                errors.append(f"duplicate metric_ref {ref}")
            metric_refs.add(ref)
            metric_count += 1
            if metric.get("configuration_id") not in config_ids:
                errors.append(f"{ref} references unknown configuration")
            if metric.get("not_source_fact") is not True:
                errors.append(f"{ref} must set not_source_fact true")
            if metric.get("not_game_balance") is not True:
                errors.append(f"{ref} must set not_game_balance true")
            for input_ref in metric.get("input_claim_refs", []):
                if input_ref not in local_claim_refs:
                    errors.append(f"{ref} references unknown input claim {input_ref}")
            for source_ref in metric.get("source_refs", []):
                if source_ref not in source_refs:
                    errors.append(f"{ref} references unknown source ref {source_ref}")

    expected_counts = {
        "entity_count": len(entities),
        "configuration_count": configuration_count,
        "technical_claim_count": claim_count,
        "normalized_numeric_claim_count": normalized_count,
        "descriptive_claim_count": descriptive_count,
        "derived_metric_count": metric_count,
        "source_ref_count": len(source_table),
    }
    for field, expected in expected_counts.items():
        if manifest.get(field) != expected:
            errors.append(
                f"manifest.{field} is {manifest.get(field)!r}; expected {expected}"
            )

    payload = {"source_table": source_table, "entities": entities}
    expected_digest = _sha256_text(_canonical_json(payload))
    if manifest.get("content_sha256") != expected_digest:
        errors.append("manifest.content_sha256 does not match bundle payload")
    boundaries = manifest.get("boundaries", {})
    if not isinstance(boundaries, dict):
        errors.append("manifest.boundaries must be an object")
    else:
        if boundaries.get("contains_source_documents") is not False:
            errors.append("bundle must not contain source documents")
        if boundaries.get("contains_game_balance") is not False:
            errors.append("bundle must not contain game balance")
    return errors


def write_godot_runtime_artifacts(
    bundle: dict[str, Any],
    profile: dict[str, Any],
    output: Path,
) -> tuple[Path, Path, dict[str, Any]]:
    config = profile["godot_runtime_bundle"]
    output.mkdir(parents=True, exist_ok=True)
    bundle_filename = str(config.get("output_filename", "ckb_runtime.json"))
    lock_filename = str(config.get("lock_filename", "ckb-lock.json"))
    bundle_path = output / bundle_filename
    bundle_text = json.dumps(bundle, ensure_ascii=False, indent=2)
    bundle_path.write_text(bundle_text, encoding="utf-8")
    bundle_file_sha256 = _sha256_text(bundle_text)

    manifest = bundle["manifest"]
    lock = {
        "lock_version": 1,
        "profile_id": manifest["profile_id"],
        "bundle_id": manifest["bundle_id"],
        "bundle_format": manifest["bundle_format"],
        "format_version": manifest["format_version"],
        "schema_version": manifest["schema_version"],
        "content_sha256": manifest["content_sha256"],
        "bundle_file_sha256": bundle_file_sha256,
        "bundle_filename": bundle_filename,
        "entity_ids": [row["id"] for row in bundle["entities"]],
        "resource_manifest": [
            {
                "path": bundle_filename,
                "sha256": bundle_file_sha256,
            }
        ],
    }
    lock_path = output / lock_filename
    lock_path.write_text(
        json.dumps(lock, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return bundle_path, lock_path, lock


def build_and_write_godot_runtime_bundle(
    entities: Iterable[Entity],
    profile: dict[str, Any],
    output: Path,
    *,
    project_root: Path = ROOT,
) -> tuple[Path | None, Path | None, dict[str, Any] | None, list[str]]:
    bundle, errors = build_godot_runtime_bundle(
        entities,
        profile,
        project_root=project_root,
    )
    if bundle is None or errors:
        return None, None, None, errors
    bundle_path, lock_path, lock = write_godot_runtime_artifacts(
        bundle,
        profile,
        output,
    )
    return bundle_path, lock_path, lock, []


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-godot-bundle")
    parser.add_argument("--canonical", type=Path, default=CANONICAL_ROOT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "godot")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    entities = load_entities(args.canonical)
    profile = load_profile(args.profile)
    bundle_path, lock_path, lock, errors = build_and_write_godot_runtime_bundle(
        entities,
        profile,
        args.output,
        project_root=ROOT,
    )
    for error in errors:
        print("ERROR:", error)
    if errors:
        if args.fail_on_error:
            raise SystemExit(1)
        return
    assert bundle_path is not None and lock_path is not None and lock is not None
    print(
        "Godot runtime bundle: "
        f"{len(lock['entity_ids'])} entities, "
        f"{lock['content_sha256']} -> {bundle_path}; lock -> {lock_path}"
    )


if __name__ == "__main__":
    main()
