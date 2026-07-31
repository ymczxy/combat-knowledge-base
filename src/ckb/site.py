from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
import json
import shutil

from .catalog import CatalogItem
from .graph import Relationship
from .model import Entity
from .visualizations import write_visualization_artifacts


def _slug(value: str) -> str:
    return value.replace(":", "__").replace("/", "_").replace(" ", "_").lower()


def _display(value: Any) -> str:
    if value is None or value == "":
        return "未记录"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (list, tuple)):
        return "、".join(_display(v) for v in value) if value else "未记录"
    if isinstance(value, dict):
        return f"`{json.dumps(value, ensure_ascii=False)}`"
    return str(value)


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _front_matter(title: str, description: str = "") -> str:
    lines = ["---", f"title: {_yaml_scalar(title)}"]
    if description:
        lines.append(f"description: {_yaml_scalar(description)}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def _table(rows: list[tuple[str, str]]) -> str:
    lines = ["| 字段 | 内容 |", "|---|---|"]
    for key, value in rows:
        safe = value.replace("\n", "<br>")
        lines.append(f"| {key} | {safe} |")
    return "\n".join(lines)


def _render_mapping(data: dict[str, Any] | None, level: int = 3) -> str:
    if not data:
        return "尚未建立。\n"
    lines: list[str] = []
    for key, value in data.items():
        label = str(key).replace("_", " ")
        if isinstance(value, dict):
            lines.append(f"{'#' * level} {label}")
            lines.append("")
            lines.append(_render_mapping(value, level + 1))
        elif isinstance(value, list):
            lines.append(f"- **{label}**：{_display(value)}")
        else:
            lines.append(f"- **{label}**：{_display(value)}")
    return "\n".join(lines) + "\n"


def entity_filename(entity: Entity) -> str:
    return _slug(entity.id) + ".md"


def render_entity_page(entity: Entity) -> str:
    classification = entity.classification
    provenance = entity.provenance
    sources = provenance.get("sources", [])
    relations = entity.relationships
    aliases = entity.aliases
    title = entity.name_zh or entity.name_en
    lines = [
        _front_matter(title, f"{entity.name_en} 的 CKB 实体页面"),
        f"# {title}",
        "",
        _table([
            ("CKB ID", f"`{entity.id}`"),
            ("英文名", entity.name_en or "未记录"),
            ("别名", _display(aliases)),
            ("实体类型", entity.entity_type),
            ("领域", _display(classification.get("domain"))),
            ("类别", _display(classification.get("class"))),
            ("子类", _display(classification.get("subclass"))),
            ("时代", _display(classification.get("eras", []))),
            ("标签", _display(classification.get("tags", []))),
            ("审核状态", _display(provenance.get("review_status"))),
        ]),
        "",
        "## 技术数据",
        "",
        _render_mapping(entity.technical),
        "## 体验配置",
        "",
        "> 这里记录的是面向游戏表现的可感知体验抽象，不等同于现实测试值。",
        "",
        _render_mapping(entity.experience_profile),
        "## 游戏配置",
        "",
        _render_mapping(entity.gameplay),
        "## 实体关系",
        "",
    ]
    if relations:
        lines.extend(["| 关系 | 目标 |", "|---|---|"])
        for relation in relations:
            target = relation.get("target_id", "")
            target_link = f"[{target}]({_slug(str(target))}.md)" if target else "未记录"
            lines.append(f"| {relation.get('type', 'related')} | {target_link} |")
    else:
        lines.append("尚未建立关系。")
    lines.extend(["", "## 来源", ""])
    if sources:
        for source in sources:
            if isinstance(source, dict):
                label = source.get("name") or source.get("source_id") or "来源"
                url = source.get("url")
                lines.append(f"- [{label}]({url})" if url else f"- {label}")
            else:
                lines.append(f"- {source}")
    else:
        lines.append("尚未登记来源。")
    lines.extend([
        "",
        "## 原始结构化数据",
        "",
        "??? note \"展开 JSON\"",
        "",
        "    ```json",
    ])
    raw_json = json.dumps(entity.raw, ensure_ascii=False, indent=2)
    lines.extend(f"    {line}" for line in raw_json.splitlines())
    lines.extend(["    ```", "", "> 本页由 CKB 自动生成，请勿直接编辑。", ""])
    return "\n".join(lines)


def _write_index(output: Path, entities: list[Entity], catalog: list[CatalogItem]) -> None:
    domains = Counter(e.classification.get("domain", "Unknown") for e in entities)
    eras = Counter(era for e in entities for era in e.classification.get("eras", []))
    priorities = Counter(item.priority for item in catalog)
    statuses = Counter(item.status for item in catalog)
    lines = [
        _front_matter("Combat Knowledge Base", "CKB 战斗知识库浏览入口"),
        "# Combat Knowledge Base",
        "",
        "CKB 将分散的武器、弹药、平台、材料、传感器和环境资料统一为可检索实体，并为《destory》生成游戏可消费数据。",
        "",
        "<div class=\"grid cards\" markdown>",
        "",
        f"-   :material-database: **{len(entities)} 个规范实体**",
        "",
        "    [浏览实体 →](entities/index.md)",
        "",
        f"-   :material-format-list-bulleted: **{len(catalog)} 条建设目录**",
        "",
        "    [浏览总目录 →](catalog/index.md)",
        "",
        f"-   :material-shape: **{len(domains)} 个已落地领域**",
        "",
        "    [按领域浏览 →](browse/domains/index.md)",
        "",
        f"-   :material-timeline-clock: **{len(eras)} 个已落地时代**",
        "",
        "    [按时代浏览 →](browse/eras/index.md)",
        "",
        "</div>",
        "",
        "## 当前状态",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 规范实体 | {len(entities)} |",
        f"| 目录候选 | {len(catalog)} |",
        f"| P0/P1 高优先级候选 | {priorities.get('P0', 0) + priorities.get('P1', 0)} |",
        f"| 已完成目录项 | {statuses.get('complete', 0)} |",
        "",
        "!!! warning \"建设中的知识库\"",
        "    目录候选不等于已核实实体。只有进入 `data/canonical` 的条目才属于规范数据。",
        "",
        "## 快速入口",
        "",
        "- [现代装备体验模型](reference/MODERN_EXPERIENCE_MODEL.md)",
        "- [数据标准](reference/DATA_STANDARD.md)",
        "- [Godot 接入](reference/GODOT_INTEGRATION.md)",
        "- [实施路线图](reference/ROADMAP.md)",
        "",
    ]
    (output / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _write_entity_indexes(output: Path, entities: list[Entity]) -> None:
    entity_root = output / "entities"
    entity_root.mkdir(parents=True, exist_ok=True)
    lines = [_front_matter("规范实体", "已经进入 CKB 主数据层的实体"), "# 规范实体", ""]
    grouped: dict[str, list[Entity]] = defaultdict(list)
    for entity in entities:
        grouped[str(entity.classification.get("domain", "Unknown"))].append(entity)
        (entity_root / entity_filename(entity)).write_text(render_entity_page(entity), encoding="utf-8")
    for domain in sorted(grouped):
        lines.extend([f"## {domain}", "", "| 中文名 | 英文名 | 类别 | 时代 | 状态 |", "|---|---|---|---|---|"])
        for entity in sorted(grouped[domain], key=lambda e: e.name_en.casefold()):
            cls = " / ".join(x for x in [entity.classification.get("class"), entity.classification.get("subclass")] if x)
            eras = ", ".join(entity.classification.get("eras", []))
            status = entity.provenance.get("review_status", "")
            lines.append(f"| [{entity.name_zh}]({entity_filename(entity)}) | {entity.name_en} | {cls} | {eras} | {status} |")
        lines.append("")
    (entity_root / "index.md").write_text("\n".join(lines), encoding="utf-8")


def _write_domain_indexes(output: Path, entities: list[Entity]) -> None:
    root = output / "browse" / "domains"
    root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[Entity]] = defaultdict(list)
    for entity in entities:
        grouped[str(entity.classification.get("domain", "Unknown"))].append(entity)
    index = [_front_matter("按领域浏览"), "# 按领域浏览", ""]
    for domain in sorted(grouped):
        filename = _slug(domain) + ".md"
        index.append(f"- [{domain}]({filename})：{len(grouped[domain])} 个实体")
        page = [_front_matter(domain), f"# {domain}", ""]
        classes: dict[str, list[Entity]] = defaultdict(list)
        for entity in grouped[domain]:
            key = " / ".join(x for x in [entity.classification.get("class"), entity.classification.get("subclass")] if x) or "未分类"
            classes[key].append(entity)
        for class_name in sorted(classes):
            page.extend([f"## {class_name}", ""])
            for entity in sorted(classes[class_name], key=lambda e: e.name_en.casefold()):
                page.append(f"- [{entity.name_zh}](../../entities/{entity_filename(entity)}) — {entity.name_en}")
            page.append("")
        (root / filename).write_text("\n".join(page), encoding="utf-8")
    (root / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def _write_era_indexes(output: Path, entities: list[Entity]) -> None:
    root = output / "browse" / "eras"
    root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[Entity]] = defaultdict(list)
    for entity in entities:
        for era in entity.classification.get("eras", []):
            grouped[str(era)].append(entity)
    index = [_front_matter("按时代浏览"), "# 按时代浏览", ""]
    for era in sorted(grouped):
        filename = _slug(era) + ".md"
        index.append(f"- [{era}]({filename})：{len(grouped[era])} 个实体")
        page = [_front_matter(era), f"# {era}", "", "| 中文名 | 英文名 | 领域 | 类别 |", "|---|---|---|---|"]
        for entity in sorted(grouped[era], key=lambda e: e.name_en.casefold()):
            page.append(
                f"| [{entity.name_zh}](../../entities/{entity_filename(entity)}) | {entity.name_en} | "
                f"{entity.classification.get('domain', '')} | {entity.classification.get('class', '')} |"
            )
        page.append("")
        (root / filename).write_text("\n".join(page), encoding="utf-8")
    (root / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def _write_catalog(output: Path, catalog: list[CatalogItem]) -> None:
    root = output / "catalog"
    groups_root = root / "groups"
    groups_root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[CatalogItem]] = defaultdict(list)
    for item in catalog:
        grouped[item.group].append(item)
    priorities = Counter(item.priority for item in catalog)
    statuses = Counter(item.status for item in catalog)
    index = [
        _front_matter("全量建设目录", "计划收录但未必已经核实的候选条目"),
        "# 全量建设目录",
        "",
        f"当前共有 **{len(catalog)}** 条候选。目录是研究队列，不等同于规范实体。",
        "",
        "## 汇总",
        "",
        "| 维度 | 数量 |",
        "|---|---:|",
    ]
    for priority, count in sorted(priorities.items()):
        index.append(f"| 优先级 {priority} | {count} |")
    for status, count in sorted(statuses.items()):
        index.append(f"| 状态 {status} | {count} |")
    index.extend(["", "## 分类目录", ""])
    for group in sorted(grouped):
        items = grouped[group]
        filename = _slug(group) + ".md"
        index.append(f"- [{group}](groups/{filename})：{len(items)} 条")
        page = [_front_matter(group), f"# {group}", "", "| 名称 | 状态 | 优先级 |", "|---|---|---|"]
        for item in sorted(items, key=lambda x: (x.priority, x.name.casefold())):
            page.append(f"| {item.name} | {item.status} | {item.priority} |")
        page.append("")
        (groups_root / filename).write_text("\n".join(page), encoding="utf-8")
    (root / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def _copy_reference_docs(project_root: Path, output: Path) -> None:
    reference = output / "reference"
    reference.mkdir(parents=True, exist_ok=True)
    for path in sorted((project_root / "docs").glob("*.md")):
        shutil.copy2(path, reference / path.name)


def _write_relationship_index(
    output: Path,
    entities: list[Entity],
    relationships: list[Relationship],
) -> None:
    """Write a stable, human-browseable relationship index for the generated site."""
    entity_names = {entity.id: (entity.name_zh or entity.name_en or entity.id) for entity in entities}
    root = output / "relationships"
    root.mkdir(parents=True, exist_ok=True)
    rows = sorted(relationships, key=lambda row: (row.source_id, row.predicate, row.target_id, row.id))
    lines = [
        _front_matter("实体关系索引", "CKB 独立关系断言浏览与查询入口"),
        "# 实体关系索引",
        "",
        f"当前共 **{len(rows)}** 条独立关系断言。关系本身保留断言 ID、方向、谓词和审核状态。",
        "",
        "| 来源实体 | 谓词 | 目标实体 | 断言 ID | 审核状态 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        source = entity_names.get(row.source_id, row.source_id)
        target = entity_names.get(row.target_id, row.target_id)
        status = row.provenance.get("review_status", "")
        source_link = f"[{source}](../entities/{_slug(row.source_id)}.md)"
        target_link = f"[{target}](../entities/{_slug(row.target_id)}.md)"
        lines.append(f"| {source_link} | `{row.predicate}` | {target_link} | `{row.id}` | {status} |")
    (root / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    query_index = {
        "schema_version": "1.0",
        "entities": [
            {
                "id": entity.id,
                "name_zh": entity.name_zh,
                "name_en": entity.name_en,
                "entity_type": entity.entity_type,
                "domain": entity.classification.get("domain"),
                "eras": entity.classification.get("eras", []),
            }
            for entity in sorted(entities, key=lambda item: item.id)
        ],
        "relationships": [row.to_dict() for row in rows],
    }
    (output / "query-index.json").write_text(
        json.dumps(query_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_site_docs(
    entities: Iterable[Entity],
    catalog: Iterable[CatalogItem],
    project_root: Path,
    output: Path,
    relationships: Iterable[Relationship] | None = None,
) -> None:
    entity_rows = list(entities)
    catalog_rows = list(catalog)
    relationship_rows = list(relationships or [])
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    _write_index(output, entity_rows, catalog_rows)
    _write_entity_indexes(output, entity_rows)
    _write_domain_indexes(output, entity_rows)
    _write_era_indexes(output, entity_rows)
    _write_catalog(output, catalog_rows)
    _write_relationship_index(output, entity_rows, relationship_rows)
    write_visualization_artifacts(entity_rows, relationship_rows, output / "visualizations")
    _copy_reference_docs(project_root, output)
