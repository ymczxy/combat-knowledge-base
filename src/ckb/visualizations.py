"""Deterministic visualization datasets and Mermaid pages for the CKB site."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import hashlib

from .graph import Relationship
from .model import Entity
from .temporal import build_temporal_index


SCHEMA_VERSION = "1.0"


def _entity_row(entity: Entity) -> dict[str, Any]:
    return {
        "id": entity.id,
        "name_en": entity.name_en,
        "name_zh": entity.name_zh,
        "entity_type": entity.entity_type,
        "domain": entity.classification.get("domain"),
        "eras": entity.classification.get("eras", []),
        "tags": entity.classification.get("tags", []),
    }


def _edge_row(row: Relationship, entity_ids: set[str]) -> dict[str, Any]:
    return {
        "id": row.id,
        "source_id": row.source_id,
        "predicate": row.predicate,
        "target_id": row.target_id,
        "confidence": row.confidence,
        "source_known": row.source_id in entity_ids,
        "target_known": row.target_id in entity_ids,
        "review_status": row.provenance.get("review_status"),
    }


def build_visualization_datasets(
    entities: Iterable[Entity],
    relationships: Iterable[Relationship],
) -> dict[str, dict[str, Any]]:
    entity_rows = list(entities)
    relation_rows = list(relationships)
    entity_ids = {entity.id for entity in entity_rows}
    nodes = [_entity_row(entity) for entity in sorted(entity_rows, key=lambda item: item.id)]
    edges = [_edge_row(row, entity_ids) for row in sorted(relation_rows, key=lambda item: item.id)]

    temporal = build_temporal_index(entity_rows)
    timeline_rows = [
        {
            "entity_id": row["entity_id"],
            "entity_name_en": row["entity_name_en"],
            "field": row["field"],
            "date": row["normalized"],
            "precision": row["precision"],
            "source_urls": row["source_urls"],
        }
        for row in temporal["rows"]
        if row["status"] == "normalized"
    ]

    map_rows = []
    for entity in entity_rows:
        location = entity.raw.get("location") or entity.raw.get("geography")
        if isinstance(location, dict) and "latitude" in location and "longitude" in location:
            map_rows.append({"entity": _entity_row(entity), "location": location})

    lineage_predicates = {"development_line_predecessor", "development_line_successor", "developed_from", "developed_into", "variant_of", "has_variant"}
    lineage_edges = [edge for edge in edges if edge["predicate"] in lineage_predicates]
    battle_edges = [edge for edge in edges if edge["predicate"] in {"participated_in", "part_of", "located_in", "armed_with", "uses_ammunition"}]
    industry_edges = [edge for edge in edges if edge["predicate"] in {"produces", "produced_by", "manufactures", "manufactured_by", "located_in"}]

    return {
        "graph": {"schema_version": SCHEMA_VERSION, "nodes": nodes, "edges": edges},
        "timeline": {"schema_version": SCHEMA_VERSION, "summary": temporal["summary"], "rows": timeline_rows},
        "map": {"schema_version": SCHEMA_VERSION, "rows": map_rows, "unlocated_entity_count": len(entity_rows) - len(map_rows)},
        "lineage": {"schema_version": SCHEMA_VERSION, "nodes": nodes, "edges": lineage_edges},
        "battle_equipment": {"schema_version": SCHEMA_VERSION, "nodes": nodes, "edges": battle_edges},
        "industry_chain": {"schema_version": SCHEMA_VERSION, "nodes": nodes, "edges": industry_edges},
    }


def _label(entity: dict[str, Any]) -> str:
    return str(entity.get("name_zh") or entity.get("name_en") or entity["id"])


def _node_key(entity_id: str) -> str:
    return "n" + hashlib.sha1(entity_id.encode("utf-8")).hexdigest()[:12]


def _mermaid_graph(payload: dict[str, Any], title: str) -> str:
    nodes = {row["id"]: row for row in payload.get("nodes", [])}
    lines = [f"# {title}", "", "```mermaid", "flowchart LR"]
    for entity_id, row in sorted(nodes.items()):
        safe_id = _node_key(entity_id)
        lines.append(f'    {safe_id}["{_label(row)}"]')
    for edge in payload.get("edges", []):
        source = _node_key(edge["source_id"])
        target = _node_key(edge["target_id"])
        if edge["source_id"] in nodes and edge["target_id"] in nodes:
            lines.append(f'    {source} -->|{edge["predicate"]}| {target}')
    lines.extend(["```", "", f"节点：{len(payload.get('nodes', []))}；边：{len(payload.get('edges', []))}。", ""])
    return "\n".join(lines)


def write_visualization_artifacts(
    entities: Iterable[Entity],
    relationships: Iterable[Relationship],
    output: Path,
) -> dict[str, dict[str, Any]]:
    datasets = build_visualization_datasets(entities, relationships)
    if output.exists():
        for path in output.glob("*"):
            if path.is_file():
                path.unlink()
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in datasets.items():
        (output / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pages = {
        "graph": "实体关系图谱",
        "timeline": "装备时间轴",
        "map": "地点地图数据",
        "lineage": "发展谱系图",
        "battle_equipment": "战役装备图",
        "industry_chain": "产业链图",
    }
    for name, title in pages.items():
        payload = datasets[name]
        if name == "timeline":
            lines = [f"# {title}", "", "| 日期 | 实体 | 字段 |", "|---|---|---|"]
            lines.extend(f"| {row['date']} | {row['entity_name_en']} | {row['field']} |" for row in payload["rows"])
            content = "\n".join(lines) + "\n"
        elif name == "map":
            content = f"# {title}\n\n地图数据点：{len(payload['rows'])}；未定位实体：{payload['unlocated_entity_count']}。\n\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
        else:
            content = _mermaid_graph(payload, title)
        (output / f"{name}.md").write_text(content, encoding="utf-8")
    return datasets
