from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import argparse
import json

from .model import Entity, load_entities
from .technical import normalize_claim


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "data" / "canonical"
DEFAULT_SPECS = ROOT / "data" / "derived" / "technical_metrics_v1_6_0_batch_08.json"


def load_metric_specs(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metric specification root must be an object")
    return payload


def _round_number(value: float) -> int | float:
    rounded = round(value, 6)
    return int(rounded) if rounded.is_integer() else rounded


def _selected_claim(
    entity: Entity,
    selector: Any,
    role: str,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(selector, dict):
        return None, f"inputs.{role} must be an object"
    claim_index = selector.get("claim_index")
    if isinstance(claim_index, bool) or not isinstance(claim_index, int):
        return None, f"inputs.{role}.claim_index must be an integer"
    expected_field = str(selector.get("expected_field", "")).strip()
    if not expected_field:
        return None, f"inputs.{role}.expected_field is required"

    technical = entity.technical
    claims = technical.get("claims", []) if isinstance(technical, dict) else []
    if not isinstance(claims, list):
        return None, "technical.claims must be an array"
    if claim_index < 0 or claim_index >= len(claims):
        return None, f"inputs.{role}.claim_index {claim_index} is out of range"
    claim = claims[claim_index]
    if not isinstance(claim, dict):
        return None, f"technical.claims[{claim_index}] must be an object"
    actual_field = str(claim.get("field", ""))
    if actual_field != expected_field:
        return None, (
            f"inputs.{role} expected field {expected_field} at claim index "
            f"{claim_index}, found {actual_field or '<missing>'}"
        )

    normalized = normalize_claim(entity, claim, claim_index)
    if normalized.get("comparison_status") != "normalized":
        return None, (
            f"inputs.{role} claim {claim_index} is not a normalized numeric claim: "
            f"{normalized.get('normalization_error') or normalized.get('comparison_status')}"
        )
    return normalized, None


def _power_to_mass(
    power: dict[str, Any],
    mass: dict[str, Any],
) -> tuple[int | float | list[int | float] | None, str | None]:
    power_normalized = power.get("normalized")
    mass_normalized = mass.get("normalized")
    if not isinstance(power_normalized, dict) or power_normalized.get("unit") != "kW":
        return None, "power input must normalize to kW"
    if not isinstance(mass_normalized, dict) or mass_normalized.get("unit") != "t":
        return None, "mass input must normalize to t"

    power_value = power_normalized.get("value")
    mass_value = mass_normalized.get("value")
    if isinstance(power_value, bool) or not isinstance(power_value, (int, float)):
        return None, "power input must be a scalar numeric value"

    mass_values: list[int | float]
    if isinstance(mass_value, bool):
        return None, "mass input must be numeric"
    if isinstance(mass_value, (int, float)):
        mass_values = [mass_value]
    elif isinstance(mass_value, list) and mass_value and all(
        not isinstance(item, bool) and isinstance(item, (int, float))
        for item in mass_value
    ):
        mass_values = list(mass_value)
    else:
        return None, "mass input must be a scalar or numeric range"
    if any(value <= 0 for value in mass_values):
        return None, "mass input must be greater than zero"

    values = sorted(_round_number(float(power_value) / float(value)) for value in mass_values)
    return (values[0] if len(values) == 1 else values), None


def _input_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_index": row.get("claim_index"),
        "field": row.get("field"),
        "original": row.get("original"),
        "normalized": row.get("normalized"),
        "qualifiers": row.get("qualifiers", {}),
        "source_urls": row.get("source_urls", []),
    }


def build_derived_metrics(
    entities: Iterable[Entity],
    specification: dict[str, Any],
) -> dict[str, Any]:
    entity_map = {entity.id: entity for entity in entities}
    metrics = specification.get("metrics", [])
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    if not str(specification.get("spec_version", "")).strip():
        errors.append("spec_version is required")
    if not isinstance(metrics, list):
        errors.append("metrics must be an array")
        metrics = []

    for index, spec in enumerate(metrics):
        prefix = f"metrics[{index}]"
        if not isinstance(spec, dict):
            errors.append(f"{prefix} must be an object")
            continue
        metric_id = str(spec.get("metric_id", "")).strip()
        if not metric_id:
            errors.append(f"{prefix}.metric_id is required")
            continue
        if metric_id in seen_ids:
            errors.append(f"{prefix}.metric_id duplicates {metric_id}")
            continue
        seen_ids.add(metric_id)

        entity_id = str(spec.get("entity_id", "")).strip()
        entity = entity_map.get(entity_id)
        if entity is None:
            errors.append(f"{metric_id}: unknown entity {entity_id or '<missing>'}")
            continue
        formula = str(spec.get("formula", "")).strip()
        if formula != "power_to_mass":
            errors.append(f"{metric_id}: unsupported formula {formula or '<missing>'}")
            continue
        inputs = spec.get("inputs")
        if not isinstance(inputs, dict):
            errors.append(f"{metric_id}: inputs must be an object")
            continue

        power, power_error = _selected_claim(entity, inputs.get("power"), "power")
        mass, mass_error = _selected_claim(entity, inputs.get("mass"), "mass")
        if power_error:
            errors.append(f"{metric_id}: {power_error}")
        if mass_error:
            errors.append(f"{metric_id}: {mass_error}")
        if power is None or mass is None:
            continue

        value, formula_error = _power_to_mass(power, mass)
        if formula_error:
            errors.append(f"{metric_id}: {formula_error}")
            continue

        source_urls = sorted({
            str(url)
            for row in (power, mass)
            for url in row.get("source_urls", [])
            if str(url)
        })
        rows.append({
            "metric_id": metric_id,
            "entity_id": entity.id,
            "entity_name_en": entity.name_en,
            "entity_name_zh": entity.name_zh,
            "metric": "power_to_mass",
            "formula": "engine_power_kW / mass_t",
            "value": value,
            "unit": "kW/t",
            "qualifiers": spec.get("qualifiers", {}),
            "inputs": {
                "power": _input_snapshot(power),
                "mass": _input_snapshot(mass),
            },
            "source_urls": source_urls,
            "derivation_status": "derived_from_normalized_public_technical_claims",
            "not_source_fact": True,
            "not_game_balance": True,
        })

    rows.sort(key=lambda row: (str(row["entity_name_en"]).casefold(), str(row["metric_id"])))
    return {
        "schema_version": "1.0",
        "spec_version": specification.get("spec_version"),
        "scope": specification.get("scope", ""),
        "summary": {
            "specification_count": len(metrics),
            "derived_metric_count": len(rows),
            "entity_count": len({row["entity_id"] for row in rows}),
            "error_count": len(errors),
        },
        "errors": errors,
        "rows": rows,
    }


def _display_value(value: Any) -> str:
    if isinstance(value, list):
        return "–".join(str(item) for item in value)
    return str(value)


def _entity_filename(entity_id: str) -> str:
    return entity_id.replace(":", "__").replace("/", "_").replace(" ", "_").lower() + ".md"


def render_derived_metrics_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines = [
        "---",
        'title: "装甲车辆派生指标"',
        'description: "使用明确输入声明计算、可完整追溯的技术派生指标"',
        "---",
        "",
        "# 装甲车辆派生指标",
        "",
        "> 本页数据不是来源原文，也不是游戏平衡值。每个结果都由明确指定的技术声明计算得到，并保留公式、输入索引、配置限定和来源。",
        "",
        "## 汇总",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 指标规格 | {summary.get('specification_count', 0)} |",
        f"| 成功生成 | {summary.get('derived_metric_count', 0)} |",
        f"| 覆盖实体 | {summary.get('entity_count', 0)} |",
        f"| 错误 | {summary.get('error_count', 0)} |",
        "",
        "## 功重比",
        "",
        "| 实体 | 结果 | 配置限定 | 功率输入 | 质量输入 | 来源 |",
        "|---|---:|---|---|---|---|",
    ]
    for row in payload.get("rows", []):
        entity_link = (
            f"[{row['entity_name_zh']}](../entities/{_entity_filename(row['entity_id'])})"
        )
        qualifiers = json.dumps(row.get("qualifiers", {}), ensure_ascii=False, sort_keys=True)
        power = row["inputs"]["power"]
        mass = row["inputs"]["mass"]
        power_text = (
            f"claim {power['claim_index']}: "
            f"{_display_value(power['normalized']['value'])} {power['normalized']['unit']}"
        )
        mass_text = (
            f"claim {mass['claim_index']}: "
            f"{_display_value(mass['normalized']['value'])} {mass['normalized']['unit']}"
        )
        sources = "<br>".join(
            f"[来源 {index + 1}]({url})"
            for index, url in enumerate(row.get("source_urls", []))
        ) or "未记录"
        lines.append(
            f"| {entity_link} | {_display_value(row['value'])} {row['unit']} | "
            f"`{qualifiers}` | {power_text} | {mass_text} | {sources} |"
        )

    if payload.get("errors"):
        lines.extend(["", "## 生成错误", ""])
        lines.extend(f"- {error}" for error in payload["errors"])

    lines.extend([
        "",
        "## 解释边界",
        "",
        "- 功重比只比较公开声明对应配置的额定功率与质量，不代表真实加速、越野能力或战斗效能。",
        "- 基础质量和附加装甲质量必须分别计算，不能自动合并。",
        "- 质量区间输出功重比区间，不取中点。",
        "- 输入 claim 索引或字段发生变化时，构建必须失败并要求人工复核。",
        "",
        "> 本页由 CKB 自动生成，请勿直接编辑。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ckb-technical-metrics")
    parser.add_argument("--canonical", type=Path, default=CANONICAL_ROOT)
    parser.add_argument("--specs", type=Path, default=DEFAULT_SPECS)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "exports" / "technical" / "derived-metrics.json",
    )
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    entities = load_entities(args.canonical)
    specification = load_metric_specs(args.specs)
    payload = build_derived_metrics(entities, specification)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(
            render_derived_metrics_markdown(payload),
            encoding="utf-8",
        )

    summary = payload["summary"]
    print(
        "Derived technical metrics: "
        f"{summary['derived_metric_count']}/{summary['specification_count']} built, "
        f"{summary['entity_count']} entities, {summary['error_count']} errors -> {args.output}"
    )
    for error in payload["errors"]:
        print("ERROR:", error)
    if args.fail_on_error and payload["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
