from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json

VALID_PRIORITIES = {"S", "A", "B", "C", "D"}


def load_source_registry(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("source registry must be a JSON array")
    return [row for row in data if isinstance(row, dict)]


def validate_source_registry(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids: list[str] = []
    for index, row in enumerate(rows):
        prefix = f"source[{index}]"
        source_id = str(row.get("source_id", "")).strip()
        ids.append(source_id)
        if not source_id:
            errors.append(f"{prefix}: missing source_id")
        if not str(row.get("name", "")).strip():
            errors.append(f"{prefix}: missing name")
        if not str(row.get("source_type", "")).strip():
            errors.append(f"{prefix}: missing source_type")
        if row.get("priority") not in VALID_PRIORITIES:
            errors.append(f"{prefix}: invalid priority {row.get('priority')!r}")
        if not str(row.get("url", "")).strip() and row.get("source_type") not in {"official", "manufacturer"}:
            errors.append(f"{prefix}: missing url")
    for source_id, count in Counter(ids).items():
        if source_id and count > 1:
            errors.append(f"duplicate source_id: {source_id}")
    return errors
