from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import csv
import json

REQUIRED_COLUMNS = [
    "name_en", "name_zh", "entity_type", "domain", "class", "subclass",
    "eras", "aliases", "source_id", "source_url",
]


@dataclass(frozen=True, slots=True)
class ImportedRecord:
    row_number: int
    source_file: str
    payload: dict[str, object]


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def load_entity_csv(path: Path) -> list[ImportedRecord]:
    records: list[ImportedRecord] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(missing)}")
        for row_number, row in enumerate(reader, start=2):
            name_en = (row.get("name_en") or "").strip()
            name_zh = (row.get("name_zh") or "").strip()
            if not name_en and not name_zh:
                raise ValueError(f"{path}:{row_number}: both names are empty")
            payload: dict[str, object] = {
                "identity": {
                    "canonical_name_en": name_en,
                    "canonical_name_zh": name_zh,
                    "aliases": _split(row.get("aliases") or ""),
                },
                "entity_type": (row.get("entity_type") or "candidate").strip() or "candidate",
                "classification": {
                    "domain": (row.get("domain") or "Mixed").strip() or "Mixed",
                    "class": (row.get("class") or "Unresolved").strip() or "Unresolved",
                    "subclass": (row.get("subclass") or "").strip() or None,
                    "eras": _split(row.get("eras") or ""),
                    "tags": _split(row.get("tags") or ""),
                },
                "provenance": {
                    "review_status": "machine_imported",
                    "sources": [{
                        "source_id": (row.get("source_id") or "manual_csv").strip() or "manual_csv",
                        "url": (row.get("source_url") or "").strip(),
                        "row_number": row_number,
                    }],
                },
                "external_ids": {
                    key.removeprefix("external_id_"): value.strip()
                    for key, value in row.items()
                    if key.startswith("external_id_") and (value or "").strip()
                },
            }
            records.append(ImportedRecord(row_number, str(path), payload))
    return records


def write_import_records(records: Iterable[ImportedRecord], output: Path) -> None:
    rows = list(records)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([
            {"row_number": row.row_number, "source_file": row.source_file, **row.payload}
            for row in rows
        ], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
