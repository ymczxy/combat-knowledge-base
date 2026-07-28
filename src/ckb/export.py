from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .model import Entity


def load_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_entities(entities: list[Entity], profile: dict[str, Any], *, allow_unverified: bool = False) -> list[Entity]:
    domains = set(profile.get("include_domains", []))
    include_unverified = bool(profile.get("include_unverified", False)) or allow_unverified
    selected: list[Entity] = []
    for entity in entities:
        if domains and entity.classification.get("domain") not in domains:
            continue
        if not include_unverified and entity.provenance.get("review_status") in {"planned", "unverified", "machine_imported"}:
            continue
        selected.append(entity)
    return selected


def write_project_bundle(entities: list[Entity], profile: dict[str, Any], output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    rows = [entity.raw for entity in entities]
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    bundle = {"manifest": {"profile_id": profile.get("profile_id", "unknown"), "entity_count": len(rows), "content_sha256": digest, "format_version": 1}, "entities": rows}
    path = output / f"ckb_{profile.get('profile_id', 'project')}.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
