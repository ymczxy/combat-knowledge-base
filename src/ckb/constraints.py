from __future__ import annotations

from dataclasses import dataclass
import re

from .adapters import SourceHit
from .candidates import CandidateEntity, normalize_name

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")

ERA_WINDOWS: dict[str, tuple[int | None, int | None]] = {
    "ANCIENT": (None, 500),
    "MEDIEVAL": (500, 1500),
    "EARLY_MODERN": (1450, 1800),
    "INDUSTRIAL": (1800, 1913),
    "WWI": (1914, 1918),
    "INTERWAR": (1919, 1938),
    "WWII": (1939, 1945),
    "EARLY_COLD_WAR": (1946, 1969),
    "LATE_COLD_WAR": (1970, 1991),
    "POST_COLD_WAR": (1992, 2001),
    "CONTEMPORARY": (2001, None),
}

CLASS_REQUIRED_TERMS: dict[str, set[str]] = {
    "Firearm": {"rifle", "gun", "pistol", "carbine", "firearm", "machine gun", "submachine gun"},
    "Missile": {"missile", "interceptor", "rocket", "surface-to-air", "anti-tank", "anti-ship"},
    "GroundVehicle": {"tank", "vehicle", "armoured", "armored", "ifv", "apc", "self-propelled"},
    "Aircraft": {"aircraft", "fighter", "bomber", "helicopter", "airplane", "aeroplane", "drone"},
    "NavalPlatform": {"ship", "destroyer", "cruiser", "submarine", "carrier", "frigate", "corvette"},
    "MeleeWeapon": {"sword", "spear", "axe", "mace", "blade", "polearm", "weapon"},
    "ProjectileWeapon": {"bow", "crossbow", "sling", "siege", "projectile weapon"},
    "Artillery": {"artillery", "cannon", "howitzer", "mortar", "gun", "rocket launcher"},
    "SensorOrElectronicSystem": {"radar", "sensor", "fire control", "electronic warfare", "combat system"},
    "UnmannedSystem": {"unmanned", "drone", "uav", "usv", "loitering munition"},
}

CLASS_FORBIDDEN_TERMS: dict[str, set[str]] = {
    "Firearm": {"video game", "film", "album", "song"},
    "Missile": {"sports team", "film", "album", "roller coaster"},
    "GroundVehicle": {"film", "video game", "band"},
    "Aircraft": {"film", "album", "sports team"},
    "NavalPlatform": {"film", "novel", "band"},
}


@dataclass(frozen=True, slots=True)
class ConstraintResult:
    adjustment: float
    compatible: bool
    matched_terms: tuple[str, ...]
    conflicts: tuple[str, ...]
    detected_years: tuple[int, ...]


def _era_bounds(eras: tuple[str, ...]) -> tuple[int | None, int | None]:
    windows = [ERA_WINDOWS[era] for era in eras if era in ERA_WINDOWS]
    starts = [start for start, _ in windows if start is not None]
    ends = [end for _, end in windows if end is not None]
    return (min(starts) if starts else None, max(ends) if ends else None)


def evaluate_constraints(candidate: CandidateEntity, hit: SourceHit) -> ConstraintResult:
    text = normalize_name(" ".join([hit.label, hit.description, *hit.aliases]))
    required = CLASS_REQUIRED_TERMS.get(candidate.class_name, set())
    forbidden = CLASS_FORBIDDEN_TERMS.get(candidate.class_name, set())

    matched = tuple(sorted(term for term in required if term in text))
    conflicts = [term for term in forbidden if term in text]

    years = tuple(sorted({int(value) for value in _YEAR_RE.findall(text)}))
    start, end = _era_bounds(candidate.eras)
    if years and (start is not None or end is not None):
        compatible_year = any((start is None or year >= start - 15) and (end is None or year <= end + 15) for year in years)
        if compatible_year:
            matched += ("era_year_compatible",)
        else:
            conflicts.append("era_year_conflict")

    adjustment = 0.0
    if required:
        adjustment += 0.10 if matched else -0.14
    adjustment -= 0.18 * len(conflicts)
    adjustment = max(-0.40, min(0.18, adjustment))

    return ConstraintResult(
        adjustment=round(adjustment, 6),
        compatible=not conflicts,
        matched_terms=matched,
        conflicts=tuple(sorted(conflicts)),
        detected_years=years,
    )
