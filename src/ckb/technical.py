from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence
import argparse
import json

from .model import Entity, load_entities


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "data" / "canonical"
NORMALIZATION_VERSION = "1.0"

# Factors convert a source unit into the dimension base unit. A field-specific
# target unit is then selected without changing the original claim.
UNIT_DEFINITIONS: dict[str, tuple[str, float]] = {
    "kg": ("mass", 1.0),
    "t": ("mass", 1000.0),
    "tonne": ("mass", 1000.0),
    "tonnes": ("mass", 1000.0),
    "short_ton": ("mass", 907.18474),
    "long_ton": ("mass", 1016.0469088),
    "m": ("length", 1.0),
    "cm": ("length", 0.01),
    "mm": ("length", 0.001),
    "km": ("length", 1000.0),
    "mi": ("length", 1609.344),
    "km/h": ("speed", 1000.0 / 3600.0),
    "mph": ("speed", 1609.344 / 3600.0),
    "m/s": ("speed", 1.0),
    "W": ("power", 1.0),
    "kW": ("power", 1000.0),
    "hp": ("power", 745.6998715822702),
    "bhp": ("power", 745.6998715822702),
    "PS": ("power", 735.49875),
    "ch": ("power", 735.49875),
    "Pa": ("pressure", 1.0),
    "kPa": ("pressure", 1000.0),
    "psi": ("pressure", 6894.757293168),
    "kg/cm2": ("pressure", 98066.5),
    "kg/cm²": ("pressure", 98066.5),
    "L": ("volume", 1.0),
    "litre": ("volume", 1.0),
    "litres": ("volume", 1.0),
    "s": ("time", 1.0),
    "min": ("time", 60.0),
    "rpm": ("rotational_speed", 1.0),
    "rounds_per_minute": ("rounds_rate", 1.0),
    "rounds/min": ("rounds_rate", 1.0),
    "degrees": ("angle", 1.0),
    "degree": ("angle", 1.0),
    "people": ("people", 1.0),
    "rounds": ("rounds", 1.0),
    "vehicles": ("vehicles", 1.0),
    "ratio": ("dimensionless", 1.0),
    "dimensionless": ("dimensionless", 1.0),
}

CANONICAL_UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "t": ("mass", 1000.0),
    "m": ("length", 1.0),
    "mm": ("length", 0.001),
    "km": ("length", 1000.0),
    "km/h": ("speed", 1000.0 / 3600.0),
    "kW": ("power", 1000.0),
    "kPa": ("pressure", 1000.0),
    "L": ("volume", 1.0),
    "s": ("time", 1.0),
    "rpm": ("rotational_speed", 1.0),
    "rounds/min": ("rounds_rate", 1.0),
    "degrees": ("angle", 1.0),
    "people": ("people", 1.0),
    "rounds": ("rounds", 1.0),
    "vehicles": ("vehicles", 1.0),
    "ratio": ("dimensionless", 1.0),
}

DESCRIPTIVE_UNITS = {"categorical", "boolean", "text", "designation"}


def _is_numeric(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return (
        isinstance(value, (list, tuple))
        and bool(value)
        and all(not isinstance(item, bool) and isinstance(item, (int, float)) for item in value)
    )


def _target_unit(field: str, source_unit: str) -> str | None:
    key = field.casefold()
    if "mass" in key or "weight" in key:
        return "t"
    if "speed" in key:
        return "km/h"
    if "power" in key:
        return "kW"
    if "pressure" in key:
        return "kPa"
    if "caliber" in key or "calibre" in key or "armour" in key or "armor" in key or "thickness" in key:
        return "mm"
    if "range" in key:
        return "km"
    if any(token in key for token in ("length", "width", "height", "clearance", "obstacle", "trench", "ford")):
        return "m"
    if key == "crew_count":
        return "people"
    if "ammunition" in key and ("count" in key or "capacity" in key):
        return "rounds"
    if "rate" in key and source_unit in {"rounds_per_minute", "rounds/min"}:
        return "rounds/min"
    if source_unit in {
        "people",
        "rounds",
        "vehicles",
        "rpm",
        "rounds_per_minute",
        "rounds/min",
        "degrees",
        "degree",
        "L",
        "litre",
        "litres",
        "ratio",
        "dimensionless",
    }:
        aliases = {
            "rounds_per_minute": "rounds/min",
            "degree": "degrees",
            "litre": "L",
            "litres": "L",
            "dimensionless": "ratio",
        }
        return aliases.get(source_unit, source_unit)

    definition = UNIT_DEFINITIONS.get(source_unit)
    if definition is None:
        return None
    dimension = definition[0]
    defaults = {
        "mass": "t",
        "length": "m",
        "speed": "km/h",
        "power": "kW",
        "pressure": "kPa",
        "volume": "L",
        "time": "s",
        "rotational_speed": "rpm",
        "rounds_rate": "rounds/min",
        "angle": "degrees",
        "people": "people",
        "rounds": "rounds",
        "vehicles": "vehicles",
        "dimensionless": "ratio",
    }
    return defaults.get(dimension)


def _round_number(value: float) -> int | float:
    rounded = round(value, 6)
    return int(rounded) if rounded.is_integer() else rounded


def _convert_number(value: int | float, source_unit: str, target_unit: str) -> int | float:
    source = UNIT_DEFINITIONS.get(source_unit)
    target = CANONICAL_UNIT_FACTORS.get(target_unit)
    if source is None:
        raise ValueError(f"unsupported source unit {source_unit}")
    if target is None:
        raise ValueError(f"unsupported target unit {target_unit}")
    if source[0] != target[0]:
        raise ValueError(
            f"unit dimension mismatch: {source_unit} ({source[0]}) -> "
            f"{target_unit} ({target[0]})"
        )
    base_value = float(value) * source[1]
    return _round_number(base_value / target[1])


def normalize_claim_value(field: str, value: Any, unit: str) -> tuple[Any, str]:
    if not _is_numeric(value):
        raise ValueError("claim value is descriptive rather than numeric")
    target_unit = _target_unit(field, unit)
    if target_unit is None:
        raise ValueError(f"unsupported unit {unit}")
    if isinstance(value, (list, tuple)):
        normalized = [_convert_number(item, unit, target_unit) for item in value]
    else:
        normalized = _convert_number(value, unit, target_unit)
    return normalized, target_unit


def normalize_claim(entity: Entity, claim: dict[str, Any], claim_index: int) -> dict[str, Any]:
    field = str(claim.get("field", ""))
    unit = str(claim.get("unit", ""))
    value = claim.get("value")
    row: dict[str, Any] = {
        "entity_id": entity.id,
        "entity_name_en": entity.name_en,
        "entity_name_zh": entity.name_zh,
        "claim_index": claim_index,
        "field": field,
        "original": {"value": value, "unit": unit},
        "qualifiers": claim.get("qualifiers", {}),
        "source_urls": claim.get("source_urls", []),
    }

    if not _is_numeric(value):
        row.update({
            "comparison_status": "descriptive",
            "normalized": None,
            "normalization_error": None,
        })
        return row

    try:
        normalized_value, normalized_unit = normalize_claim_value(field, value, unit)
    except ValueError as exc:
        row.update({
            "comparison_status": "unsupported_numeric",
            "normalized": None,
            "normalization_error": str(exc),
        })
        return row

    row.update({
        "comparison_status": "normalized",
        "normalized": {"value": normalized_value, "unit": normalized_unit},
        "normalization_error": None,
    })
    return row


def _field_summary(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("field", ""))].append(row)
    summary: dict[str, dict[str, Any]] = {}
    for field in sorted(grouped):
        field_rows = grouped[field]
        normalized_units = sorted({
            str(row["normalized"]["unit"])
            for row in field_rows
            if isinstance(row.get("normalized"), dict)
        })
        summary[field] = {
            "claim_count": len(field_rows),
            "normalized_count": sum(row.get("comparison_status") == "normalized" for row in field_rows),
            "descriptive_count": sum(row.get("comparison_status") == "descriptive" for row in field_rows),
            "unsupported_numeric_count": sum(
                row.get("comparison_status") == "unsupported_numeric" for row in field_rows
            ),
            "canonical_units": normalized_units,
        }
    return summary


def build_technical_comparison(
    entities: Iterable[Entity],
    *,
    fields: Sequence[str] | None = None,
    entity_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    field_filter = {value for value in fields or []}
    entity_filter = {value for value in entity_ids or []}
    rows: list[dict[str, Any]] = []
    profile_entity_ids: set[str] = set()

    for entity in entities:
        if entity_filter and entity.id not in entity_filter:
            continue
        technical = entity.technical
        if not isinstance(technical, dict):
            continue
        claims = technical.get("claims", [])
        if not isinstance(claims, list) or not claims:
            continue
        profile_entity_ids.add(entity.id)
        for claim_index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                continue
            field = str(claim.get("field", ""))
            if field_filter and field not in field_filter:
                continue
            rows.append(normalize_claim(entity, claim, claim_index))

    rows.sort(key=lambda row: (
        str(row.get("field", "")),
        str(row.get("entity_name_en", "")).casefold(),
        json.dumps(row.get("qualifiers", {}), sort_keys=True, ensure_ascii=False),
        int(row.get("claim_index", 0)),
    ))
    normalized_count = sum(row.get("comparison_status") == "normalized" for row in rows)
    descriptive_count = sum(row.get("comparison_status") == "descriptive" for row in rows)
    unsupported_rows = [
        row for row in rows if row.get("comparison_status") == "unsupported_numeric"
    ]
    numeric_count = normalized_count + len(unsupported_rows)

    return {
        "schema_version": "1.0",
        "normalization_version": NORMALIZATION_VERSION,
        "filters": {
            "fields": sorted(field_filter),
            "entity_ids": sorted(entity_filter),
        },
        "summary": {
            "profile_entity_count": len(profile_entity_ids),
            "claim_count": len(rows),
            "numeric_claim_count": numeric_count,
            "normalized_numeric_claim_count": normalized_count,
            "descriptive_claim_count": descriptive_count,
            "unsupported_numeric_count": len(unsupported_rows),
            "comparison_field_count": len({str(row.get("field", "")) for row in rows}),
        },
        "field_summary": _field_summary(rows),
        "unsupported_numeric_claims": unsupported_rows,
        "rows": rows,
    }


def technical_normalization_errors(entity: Entity) -> list[str]:
    payload = build_technical_comparison([entity])
    return [
        f"technical.claims[{row['claim_index']}] {row['field']}: {row['normalization_error']}"
        for row in payload["unsupported_numeric_claims"]
    ]


def _display_value(value: Any) -> str:
    if isinstance(value, list):
        return "–".join(str(item) for item in value)
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _entity_filename(entity_id: str) -> str:
    return entity_id.replace(":", "__").replace("/", "_").replace(" ", "_").lower() + ".md"


def render_technical_comparison_markdown(
    entities: Iterable[Entity],
    *,
    fields: Sequence[str] | None = None,
    entity_ids: Sequence[str] | None = None,
) -> str:
    payload = build_technical_comparison(
        entities,
        fields=fields,
        entity_ids=entity_ids,
    )
    summary = payload["summary"]
    rows = payload["rows"]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["field"])].append(row)

    lines = [
        "---",
        'title: "技术参数比较"',
        'description: "保留原始技术声明并生成统一单位的比较视图"',
        "---",
        "",
        "# 技术参数比较",
        "",
        "> 标准值是由原始公开声明按确定性单位规则换算得到的派生视图。原值、配置限定和来源仍然保留；本页不会从多个改型中自行选择一个代表值。",
        "",
        "## 汇总",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 已建立技术档案的实体 | {summary['profile_entity_count']} |",
        f"| 技术声明 | {summary['claim_count']} |",
        f"| 已标准化数值声明 | {summary['normalized_numeric_claim_count']} |",
        f"| 描述性声明 | {summary['descriptive_claim_count']} |",
        f"| 不支持的数值声明 | {summary['unsupported_numeric_count']} |",
        "",
    ]

    for field in sorted(grouped):
        field_rows = grouped[field]
        lines.extend([
            f"## `{field}`",
            "",
            "| 实体 | 标准值 | 原始声明 | 配置限定 | 来源 |",
            "|---|---:|---:|---|---|",
        ])
        for row in field_rows:
            entity_link = (
                f"[{row['entity_name_zh']}](../entities/{_entity_filename(row['entity_id'])})"
            )
            normalized = row.get("normalized")
            standard = (
                f"{_display_value(normalized['value'])} {normalized['unit']}"
                if isinstance(normalized, dict)
                else "—"
            )
            original = row["original"]
            original_text = f"{_display_value(original['value'])} {original['unit']}"
            qualifiers = json.dumps(row.get("qualifiers", {}), ensure_ascii=False, sort_keys=True)
            sources = "<br>".join(
                f"[来源 {index + 1}]({url})"
                for index, url in enumerate(row.get("source_urls", []))
            ) or "未记录"
            lines.append(
                f"| {entity_link} | {standard} | {original_text} | `{qualifiers}` | {sources} |"
            )
        lines.append("")

    if payload["unsupported_numeric_claims"]:
        lines.extend([
            "## 无法标准化的数值声明",
            "",
            "| 实体 | 字段 | 单位 | 原因 |",
            "|---|---|---|---|",
        ])
        for row in payload["unsupported_numeric_claims"]:
            lines.append(
                f"| `{row['entity_id']}` | `{row['field']}` | `{row['original']['unit']}` | "
                f"{row['normalization_error']} |"
            )
        lines.append("")

    lines.extend([
        "## 使用边界",
        "",
        "- 标准化只处理单位，不解决不同改型、年代、装甲套件、路面条件或测试口径之间的语义差异。",
        "- 同一字段出现多条记录是预期行为，调用方必须结合 `qualifiers` 选择所需配置。",
        "- 体验档案和游戏平衡值不参与本页的现实参数排序。",
        "",
        "> 本页由 CKB 自动生成，请勿直接编辑。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-technical")
    parser.add_argument("--canonical", type=Path, default=CANONICAL_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "exports" / "technical" / "comparison.json",
    )
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--field", action="append", default=[])
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--fail-on-unsupported", action="store_true")
    args = parser.parse_args()

    entities = load_entities(args.canonical)
    payload = build_technical_comparison(
        entities,
        fields=args.field,
        entity_ids=args.entity,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(
            render_technical_comparison_markdown(
                entities,
                fields=args.field,
                entity_ids=args.entity,
            ),
            encoding="utf-8",
        )

    summary = payload["summary"]
    print(
        "Technical comparison: "
        f"{summary['claim_count']} claims, "
        f"{summary['normalized_numeric_claim_count']} normalized, "
        f"{summary['descriptive_claim_count']} descriptive, "
        f"{summary['unsupported_numeric_count']} unsupported -> {args.output}"
    )
    if args.fail_on_unsupported and summary["unsupported_numeric_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
