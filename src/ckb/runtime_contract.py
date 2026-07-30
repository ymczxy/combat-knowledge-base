from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import hashlib
import json

from .godot_bundle import (
    BUNDLE_FORMAT,
    BUNDLE_SCHEMA_VERSION,
    validate_godot_runtime_bundle,
)


SUPPORTED_FORMAT_VERSION = 1
SUPPORTED_LOCK_VERSION = 1


def _load_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"{label} does not exist: {path}"]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"{label} could not be read: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"{label} root must be an object"]
    return payload, []


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_runtime_contract(
    bundle_path: Path,
    lock_path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    bundle, bundle_errors = _load_json_object(bundle_path, "runtime bundle")
    lock, lock_errors = _load_json_object(lock_path, "runtime lock")
    errors = [*bundle_errors, *lock_errors]
    if bundle is None or lock is None:
        return None, errors

    errors.extend(validate_godot_runtime_bundle(bundle))
    manifest = bundle.get("manifest")
    if not isinstance(manifest, dict):
        return None, errors or ["runtime bundle manifest must be an object"]

    if lock.get("lock_version") != SUPPORTED_LOCK_VERSION:
        errors.append(
            f"unsupported lock_version {lock.get('lock_version')!r}; "
            f"expected {SUPPORTED_LOCK_VERSION}"
        )
    if manifest.get("bundle_format") != BUNDLE_FORMAT:
        errors.append(
            f"unsupported bundle_format {manifest.get('bundle_format')!r}; "
            f"expected {BUNDLE_FORMAT}"
        )
    if manifest.get("format_version") != SUPPORTED_FORMAT_VERSION:
        errors.append(
            f"unsupported format_version {manifest.get('format_version')!r}; "
            f"expected {SUPPORTED_FORMAT_VERSION}"
        )
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        errors.append(
            f"unsupported schema_version {manifest.get('schema_version')!r}; "
            f"expected {BUNDLE_SCHEMA_VERSION}"
        )

    mirrored_fields = (
        "profile_id",
        "bundle_id",
        "bundle_format",
        "format_version",
        "schema_version",
        "content_sha256",
    )
    for field in mirrored_fields:
        if lock.get(field) != manifest.get(field):
            errors.append(
                f"lock.{field} does not match manifest.{field}: "
                f"{lock.get(field)!r} != {manifest.get(field)!r}"
            )

    if lock.get("bundle_filename") != bundle_path.name:
        errors.append(
            f"lock.bundle_filename is {lock.get('bundle_filename')!r}; "
            f"expected {bundle_path.name!r}"
        )

    try:
        actual_file_sha256 = _sha256_file(bundle_path)
    except OSError as exc:
        errors.append(f"runtime bundle hash could not be calculated: {exc}")
        actual_file_sha256 = ""
    if lock.get("bundle_file_sha256") != actual_file_sha256:
        errors.append(
            "lock.bundle_file_sha256 does not match the runtime bundle file"
        )

    entity_rows = bundle.get("entities", [])
    actual_entity_ids = [
        str(row.get("id", ""))
        for row in entity_rows
        if isinstance(row, dict)
    ] if isinstance(entity_rows, list) else []
    locked_entity_ids = lock.get("entity_ids")
    if not isinstance(locked_entity_ids, list):
        errors.append("lock.entity_ids must be an array")
    elif [str(value) for value in locked_entity_ids] != actual_entity_ids:
        errors.append("lock.entity_ids does not match the Bundle entity order")

    resource_manifest = lock.get("resource_manifest")
    if not isinstance(resource_manifest, list) or len(resource_manifest) != 1:
        errors.append("lock.resource_manifest must contain exactly one runtime Bundle row")
    else:
        resource = resource_manifest[0]
        if not isinstance(resource, dict):
            errors.append("lock.resource_manifest[0] must be an object")
        else:
            if resource.get("path") != bundle_path.name:
                errors.append("lock.resource_manifest[0].path does not match Bundle filename")
            if resource.get("sha256") != actual_file_sha256:
                errors.append("lock.resource_manifest[0].sha256 does not match Bundle file")

    summary = {
        "bundle_format": manifest.get("bundle_format"),
        "format_version": manifest.get("format_version"),
        "schema_version": manifest.get("schema_version"),
        "entity_count": manifest.get("entity_count"),
        "configuration_count": manifest.get("configuration_count"),
        "technical_claim_count": manifest.get("technical_claim_count"),
        "derived_metric_count": manifest.get("derived_metric_count"),
        "source_ref_count": manifest.get("source_ref_count"),
        "content_sha256": manifest.get("content_sha256"),
        "bundle_file_sha256": actual_file_sha256,
        "error_count": len(errors),
    }
    return summary, errors


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-runtime-contract")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    summary, errors = validate_runtime_contract(args.bundle, args.lock)
    if args.output and summary is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if summary is not None:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    for error in errors:
        print("ERROR:", error)
    if errors and args.fail_on_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
