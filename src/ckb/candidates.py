from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable
import json
import re
import unicodedata

from .catalog import CatalogItem

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

GROUP_CLASSIFICATION: dict[str, tuple[str, str, str | None, list[str]]] = {
    "ancient_and_medieval_melee": ("Weapon", "MeleeWeapon", None, ["ANCIENT", "MEDIEVAL"]),
    "projectile_and_siege": ("Weapon", "ProjectileWeapon", None, ["ANCIENT", "MEDIEVAL"]),
    "early_gunpowder": ("Weapon", "EarlyGunpowderWeapon", None, ["EARLY_MODERN"]),
    "industrial_and_wwi_small_arms": ("Weapon", "Firearm", None, ["INDUSTRIAL", "WWI"]),
    "wwi_artillery_and_platforms": ("Weapon", "Artillery", None, ["WWI"]),
    "wwii_small_arms": ("Weapon", "Firearm", None, ["WWII"]),
    "wwii_armored_vehicles": ("Platform", "GroundVehicle", None, ["WWII"]),
    "wwii_aircraft": ("Platform", "Aircraft", None, ["WWII"]),
    "wwii_naval": ("Platform", "NavalPlatform", None, ["WWII"]),
    "early_cold_war": ("Mixed", "Unresolved", None, ["EARLY_COLD_WAR"]),
    "late_cold_war": ("Mixed", "Unresolved", None, ["LATE_COLD_WAR"]),
    "contemporary_small_arms": ("Weapon", "Firearm", None, ["CONTEMPORARY"]),
    "contemporary_ground": ("Platform", "GroundVehicle", None, ["CONTEMPORARY"]),
    "contemporary_air": ("Platform", "Aircraft", None, ["CONTEMPORARY"]),
    "contemporary_naval": ("Platform", "NavalPlatform", None, ["CONTEMPORARY"]),
    "contemporary_missiles_and_air_defense": ("Weapon", "Missile", None, ["CONTEMPORARY"]),
    "unmanned_and_loitering_systems": ("Platform", "UnmannedSystem", None, ["CONTEMPORARY"]),
    "sensors_fire_control_and_ew": ("System", "SensorOrElectronicSystem", None, ["LATE_COLD_WAR", "CONTEMPORARY"]),
}


@dataclass(frozen=True, slots=True)
class CandidateEntity:
    candidate_id: str
    source_group: str
    source_name: str
    normalized_name: str
    domain: str
    class_name: str
    subclass: str | None
    eras: tuple[str, ...]
    priority: str
    catalog_status: str
    resolution_status: str
    ambiguity_key: str | None = None

    def to_dict(self) -> dict[str, object]:
        row = asdict(self)
        row["class"] = row.pop("class_name")
        row["eras"] = list(self.eras)
        return row

    def to_draft(self) -> dict[str, object]:
        entity_type = {
            "Weapon": "weapon",
            "Platform": "platform",
            "System": "system",
        }.get(self.domain, "candidate")
        return {
            "id": self.candidate_id,
            "entity_type": entity_type,
            "identity": {
                "canonical_name_en": self.source_name,
                "canonical_name_zh": "",
                "aliases": [],
            },
            "classification": {
                "domain": self.domain,
                "class": self.class_name,
                "subclass": self.subclass,
                "eras": list(self.eras),
                "tags": ["catalog_candidate", f"priority_{self.priority.casefold()}"],
            },
            "relationships": [],
            "technical": None,
            "experience_profile": None,
            "gameplay": {"status": "not_started"},
            "provenance": {
                "review_status": "machine_imported",
                "sources": [{
                    "source_id": "ckb_catalog",
                    "catalog_group": self.source_group,
                    "catalog_name": self.source_name,
                    "catalog_status": self.catalog_status,
                }],
                "resolution": {
                    "status": self.resolution_status,
                    "normalized_name": self.normalized_name,
                    "ambiguity_key": self.ambiguity_key,
                },
            },
            "rights": {"rights_status": "deferred"},
        }


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = normalized.replace("×", "x").replace("–", "-").replace("—", "-")
    return " ".join(normalized.split())


def stable_slug(value: str) -> str:
    canonical = normalize_name(value)
    normalized = unicodedata.normalize("NFKD", canonical)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").casefold()
    slug = _NON_ALNUM.sub("_", ascii_value).strip("_")
    if slug:
        return slug
    digest = sha1(canonical.encode("utf-8")).hexdigest()[:12]
    return f"u_{digest}"


def candidate_id(item: CatalogItem) -> str:
    return f"ckb:candidate:{stable_slug(item.group)}:{stable_slug(item.name)}"


def classify_group(group: str) -> tuple[str, str, str | None, list[str]]:
    return GROUP_CLASSIFICATION.get(group, ("Mixed", "Unresolved", None, []))


def build_candidates(items: Iterable[CatalogItem]) -> list[CandidateEntity]:
    rows = list(items)
    name_groups: dict[str, set[str]] = defaultdict(set)
    for item in rows:
        name_groups[normalize_name(item.name)].add(item.group)

    candidates: list[CandidateEntity] = []
    for item in rows:
        domain, class_name, subclass, eras = classify_group(item.group)
        key = normalize_name(item.name)
        ambiguous = len(name_groups[key]) > 1 or domain == "Mixed"
        candidates.append(CandidateEntity(
            candidate_id=candidate_id(item),
            source_group=item.group,
            source_name=item.name,
            normalized_name=key,
            domain=domain,
            class_name=class_name,
            subclass=subclass,
            eras=tuple(eras),
            priority=item.priority,
            catalog_status=item.status,
            resolution_status="ambiguous" if ambiguous else "unresolved",
            ambiguity_key=key if ambiguous else None,
        ))
    return candidates


def ambiguity_groups(candidates: Iterable[CandidateEntity]) -> dict[str, list[CandidateEntity]]:
    grouped: dict[str, list[CandidateEntity]] = defaultdict(list)
    for candidate in candidates:
        if candidate.ambiguity_key:
            grouped[candidate.ambiguity_key].append(candidate)
    return dict(sorted(grouped.items()))


def write_candidate_bundle(candidates: Iterable[CandidateEntity], output: Path) -> None:
    rows = list(candidates)
    output.mkdir(parents=True, exist_ok=True)
    (output / "candidates.json").write_text(
        json.dumps([row.to_dict() for row in rows], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    ambiguities = {
        key: [row.to_dict() for row in group]
        for key, group in ambiguity_groups(rows).items()
    }
    (output / "ambiguities.json").write_text(
        json.dumps(ambiguities, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest = {
        "format_version": 1,
        "candidate_count": len(rows),
        "ambiguity_key_count": len(ambiguities),
        "resolved_count": sum(row.resolution_status == "resolved" for row in rows),
        "unresolved_count": sum(row.resolution_status == "unresolved" for row in rows),
        "ambiguous_count": sum(row.resolution_status == "ambiguous" for row in rows),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_drafts(candidates: Iterable[CandidateEntity], output: Path) -> None:
    rows = list(candidates)
    output.mkdir(parents=True, exist_ok=True)
    for candidate in rows:
        filename = candidate.candidate_id.replace(":", "__") + ".json"
        (output / filename).write_text(
            json.dumps(candidate.to_draft(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    (output / "manifest.json").write_text(
        json.dumps({"format_version": 1, "draft_count": len(rows)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
