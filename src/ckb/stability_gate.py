"""v2.0 release gate covering schema, governance, queries, temporal and runtime contracts."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import argparse
import json

from .assertions import aggregate_assertions
from .compatibility import CURRENT_RELEASE, check_runtime_compatibility, migration_policy
from .content_audit import build_content_report, load_content_batches
from .godot_bundle import build_and_write_godot_runtime_bundle
from .graph import KnowledgeGraph, load_relationships
from .model import load_entities
from .predicates import load_predicate_registry
from .query import related_entities, search_entities
from .runtime_contract import validate_runtime_contract
from .technical import build_technical_comparison
from .temporal import build_temporal_index
from .validation import validate_all
from .visualizations import write_visualization_artifacts

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PROFILE_NAMES = (
    "build_profile.json",
    "small_arms_build_profile.json",
    "aviation_build_profile.json",
    "naval_build_profile.json",
    "integrated_systems_build_profile.json",
    "game_build_profile_v1.json",
    "game_build_profile.json",
)


def run_stability_gate(project_root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    entities = load_entities(project_root / "data" / "canonical")
    relationships = load_relationships(project_root / "data" / "relationships")
    registry = load_predicate_registry(project_root / "data" / "ontology" / "predicates.json")
    graph = KnowledgeGraph(entities, relationships, predicate_registry=registry)
    errors.extend(validate_all(entities))
    errors.extend(registry.validate())
    errors.extend(graph.validate())
    governance = aggregate_assertions(relationships, registry)
    if governance.conflicts:
        errors.append(f"relationship conflicts: {len(governance.conflicts)}")

    technical = build_technical_comparison(entities)
    if technical["summary"]["unsupported_numeric_count"]:
        errors.append("unsupported numeric technical claims remain")
    temporal = build_temporal_index(entities)
    if temporal["summary"]["unparsed_count"]:
        errors.append("unparsed temporal claims remain")
    batches = load_content_batches(project_root / "data" / "content_batches")
    content = build_content_report(entities, relationships, batches)

    schema_path = project_root / "schemas" / "godot_runtime_bundle.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if "relationships" not in schema.get("required", []):
            errors.append("runtime schema does not require relationships")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"runtime schema unreadable: {exc}")

    release_path = project_root / "data" / "releases" / "v2_0_0.json"
    try:
        release = json.loads(release_path.read_text(encoding="utf-8"))
        if release.get("release_version") != CURRENT_RELEASE or release.get("status") != "released":
            errors.append("v2.0 release manifest is not released")
        snapshot = release.get("content_snapshot", {})
        actual_content_snapshot = {
            "canonical_entity_count": len(entities),
            "relationship_assertion_count": len(relationships),
            "embedded_relationship_count": content["embedded_relationship_count"],
            "content_batch_count": content["content_batch_count"],
            "source_checked_entity_count": content["review_status_counts"].get(
                "source_checked",
                0,
            ),
            "technical_profile_count": technical["summary"]["profile_entity_count"],
            "technical_claim_count": technical["summary"]["claim_count"],
            "normalized_numeric_claim_count": technical["summary"][
                "normalized_numeric_claim_count"
            ],
            "descriptive_claim_count": technical["summary"]["descriptive_claim_count"],
            "unsupported_numeric_claim_count": technical["summary"][
                "unsupported_numeric_count"
            ],
        }
        for key, value in actual_content_snapshot.items():
            if snapshot.get(key) != value:
                errors.append(f"release snapshot mismatch: {key}")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"release manifest unreadable: {exc}")
        release = {}

    query_rows = search_entities(entities, text="Normandy", entity_type="place")
    if [row.id for row in query_rows] != ["ckb:place:region:normandy"]:
        errors.append("stable query search result mismatch")
    related = related_entities(graph, "ckb:system:air_defense:patriot", predicate="uses_sensor", direction="out")
    if [row.id for row in related] != ["ckb:component:sensor:patriot_an_mpq_65"]:
        errors.append("stable query relationship result mismatch")

    visualization_dir = project_root / "exports" / ".stability_visualizations"
    visualization_payloads = write_visualization_artifacts(entities, relationships, visualization_dir)
    expected_visualizations = {
        "graph",
        "timeline",
        "map",
        "lineage",
        "battle_equipment",
        "industry_chain",
        "factory_location",
        "unit_organization",
    }
    if set(visualization_payloads) != expected_visualizations:
        errors.append("visualization contract mismatch: expected all roadmap datasets")

    runtime_summaries: dict[str, Any] = {}
    for profile_name in RUNTIME_PROFILE_NAMES:
        with TemporaryDirectory() as directory:
            profile = json.loads((project_root / "data" / "curated" / "destory" / profile_name).read_text(encoding="utf-8"))
            bundle_path, lock_path, _, build_errors = build_and_write_godot_runtime_bundle(
                entities,
                profile,
                Path(directory),
                project_root=project_root,
                relationships=relationships,
            )
            errors.extend(build_errors)
            if bundle_path is not None and lock_path is not None:
                summary, contract_errors = validate_runtime_contract(bundle_path, lock_path)
                errors.extend(contract_errors)
                summary["profile_id"] = profile.get("profile_id", "")
                runtime_summaries[profile_name] = summary

    release_runtime_snapshots = release.get("godot_runtime_snapshots", {})
    if set(release_runtime_snapshots) != set(RUNTIME_PROFILE_NAMES):
        errors.append("release runtime snapshot profile matrix mismatch")
    runtime_snapshot_fields = (
        "profile_id",
        "entity_count",
        "configuration_count",
        "technical_claim_count",
        "derived_metric_count",
        "source_ref_count",
        "relationship_assertion_count",
        "content_sha256",
        "bundle_file_sha256",
    )
    for profile_name in RUNTIME_PROFILE_NAMES:
        expected = release_runtime_snapshots.get(profile_name, {})
        actual = runtime_summaries.get(profile_name, {})
        for field_name in runtime_snapshot_fields:
            if expected.get(field_name) != actual.get(field_name):
                errors.append(
                    "release runtime snapshot mismatch: "
                    f"{profile_name}:{field_name}"
                )

    summary = {
        "release": CURRENT_RELEASE,
        "entity_count": len(entities),
        "relationship_count": len(relationships),
        "technical_claim_count": technical["summary"]["claim_count"],
        "temporal": temporal["summary"],
        "content": content,
        "query_search_count": len(query_rows),
        "query_related_count": len(related),
        "visualization_dataset_count": len(visualization_payloads),
        "runtime": runtime_summaries,
        "compatibility": migration_policy(),
        "error_count": len(errors),
    }
    return summary, errors


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-stability-gate")
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "release" / "v2_0_stability.json")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()
    summary, errors = run_stability_gate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for error in errors:
        print("ERROR:", error)
    if errors and args.fail_on_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
