"""v2.0 compatibility policy for serialized CKB and Godot runtime contracts."""

from __future__ import annotations

from typing import Any

CURRENT_RELEASE = "2.0.0"
SUPPORTED_SCHEMA_VERSION = "1.0"
SUPPORTED_BUNDLE_FORMAT = "ckb.godot.runtime"
SUPPORTED_BUNDLE_FORMAT_VERSION = 1
SUPPORTED_LOCK_VERSION = 1


def check_runtime_compatibility(manifest: dict[str, Any], lock: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if manifest.get("bundle_format") != SUPPORTED_BUNDLE_FORMAT:
        errors.append("unsupported bundle_format")
    if manifest.get("format_version") != SUPPORTED_BUNDLE_FORMAT_VERSION:
        errors.append("unsupported Bundle format_version")
    if manifest.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    if lock is not None and lock.get("lock_version") != SUPPORTED_LOCK_VERSION:
        errors.append("unsupported lock_version")
    return errors


def migration_policy() -> dict[str, Any]:
    return {
        "current_release": CURRENT_RELEASE,
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "bundle_format": SUPPORTED_BUNDLE_FORMAT,
        "bundle_format_version": SUPPORTED_BUNDLE_FORMAT_VERSION,
        "lock_version": SUPPORTED_LOCK_VERSION,
        "rules": [
            {"from": "1.x", "to": "2.0.0", "action": "read-only compatibility; preserve unknown fields and re-export through v2 schema"},
            {"from": "ckb.godot.runtime@1", "to": "ckb.godot.runtime@1", "action": "compatible; relationship_assertions may be absent and are treated as empty for legacy bundles"},
            {"from": "embedded entity relationships", "to": "independent assertions", "action": "migration required; do not silently infer or overwrite provenance"},
        ],
        "rollback": "Keep the prior Bundle/Lock pair and release manifest; never overwrite a locked artifact in place.",
    }
