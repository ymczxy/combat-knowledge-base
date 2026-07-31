"""Deterministic normalization for public historical date claims."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
import argparse
import json
import re

from .model import Entity, load_entities

ROOT = Path(__file__).resolve().parents[2]
DATE_FIELDS = {"date", "start_date", "end_date", "formation_date", "service_start", "service_end"}
DATE_PATTERNS = ("%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%Y/%m/%d")


def normalize_historical_date(value: Any) -> dict[str, Any]:
    original = str(value).strip()
    for pattern in DATE_PATTERNS:
        try:
            parsed = datetime.strptime(original, pattern).date()
        except ValueError:
            continue
        return {"original": original, "normalized": parsed.isoformat(), "precision": "day", "status": "normalized"}
    year_match = re.fullmatch(r"(\d{4})", original)
    if year_match:
        return {"original": original, "normalized": f"{year_match.group(1)}-01-01", "precision": "year", "status": "normalized"}
    return {"original": original, "normalized": None, "precision": None, "status": "unparsed"}


def build_temporal_index(entities: Iterable[Entity]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for entity in entities:
        claims = entity.technical.get("claims", []) if isinstance(entity.technical, dict) else []
        for index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                continue
            field = str(claim.get("field", ""))
            qualifiers = claim.get("qualifiers", {})
            qualifier_date = qualifiers.get("date") if isinstance(qualifiers, dict) else None
            if field in DATE_FIELDS:
                value = claim.get("value")
                value_source = "claim_value"
            elif qualifier_date is not None:
                value = qualifier_date
                value_source = "qualifier.date"
            else:
                continue
            normalized = normalize_historical_date(value)
            rows.append({
                "entity_id": entity.id,
                "entity_name_en": entity.name_en,
                "claim_index": index,
                "field": claim.get("field"),
                "qualifiers": qualifiers,
                "value_source": value_source,
                "source_urls": claim.get("source_urls", []),
                **normalized,
            })
    rows.sort(key=lambda row: (row["normalized"] or "9999-99-99", row["entity_id"], row["claim_index"]))
    return {
        "schema_version": "1.0",
        "normalization_version": "1.0",
        "summary": {
            "date_claim_count": len(rows),
            "normalized_count": sum(row["status"] == "normalized" for row in rows),
            "unparsed_count": sum(row["status"] == "unparsed" for row in rows),
            "entity_count": len({row["entity_id"] for row in rows}),
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-temporal")
    parser.add_argument("--canonical", type=Path, default=ROOT / "data" / "canonical")
    parser.add_argument("--output", type=Path, default=ROOT / "exports" / "temporal" / "index.json")
    args = parser.parse_args()
    payload = build_temporal_index(load_entities(args.canonical))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = payload["summary"]
    print(f"Temporal index: {summary['date_claim_count']} claims, {summary['normalized_count']} normalized, {summary['unparsed_count']} unparsed -> {args.output}")
    if summary["unparsed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
