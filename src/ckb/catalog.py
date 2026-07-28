from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import csv

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"planned", "researching", "draft", "reviewed", "complete", "deferred"}


@dataclass(frozen=True, slots=True)
class CatalogItem:
    group: str
    name: str
    status: str
    priority: str
    source_file: str


def load_catalog(root: Path) -> list[CatalogItem]:
    items: list[CatalogItem] = []
    groups_root = root / "groups"
    for path in sorted(groups_root.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["name", "status", "priority"]:
                raise ValueError(f"{path}: expected name,status,priority columns")
            group = path.stem
            for line_no, row in enumerate(reader, start=2):
                name = (row.get("name") or "").strip()
                status = (row.get("status") or "").strip()
                priority = (row.get("priority") or "").strip()
                if not name:
                    raise ValueError(f"{path}:{line_no}: empty name")
                items.append(CatalogItem(group, name, status, priority, str(path)))
    return items


def validate_catalog(items: list[CatalogItem]) -> list[str]:
    errors: list[str] = []
    for item in items:
        if item.status not in VALID_STATUSES:
            errors.append(f"{item.source_file}: {item.name}: invalid status {item.status!r}")
        if item.priority not in VALID_PRIORITIES:
            errors.append(f"{item.source_file}: {item.name}: invalid priority {item.priority!r}")
    normalized = Counter((item.group, item.name.casefold().strip()) for item in items)
    for (group, name), count in normalized.items():
        if count > 1:
            errors.append(f"catalog duplicate candidate in {group}: {name} ({count})")
    return errors


def catalog_stats(items: list[CatalogItem]) -> dict[str, object]:
    return {
        "total": len(items),
        "groups": dict(sorted(Counter(item.group for item in items).items())),
        "priorities": dict(sorted(Counter(item.priority for item in items).items())),
        "statuses": dict(sorted(Counter(item.status for item in items).items())),
    }
